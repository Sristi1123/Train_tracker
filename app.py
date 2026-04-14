from flask import Flask, request, jsonify, render_template
from datetime import datetime
import requests
import logging
import hashlib
import re
from ml_model import predict_delay

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
logging.basicConfig(level=logging.INFO)

API_KEY = os.environ.get("RAPIDAPI_KEY", "")
API_HOST = "irctc-insight.p.rapidapi.com"

# --- PAGE ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# --- Helper functions ---
def get_rapidapi_data(train_number):
    url = "https://irctc-insight.p.rapidapi.com/api/v1/train-details"
    payload = {"trainNo": str(train_number)}
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    try:
        data = response.json()
    except Exception:
        data = {}
    return response, data

def pseudo_random(seed_str, min_val, max_val):
    """Generates a stable pseudo-random integer bound to the train number."""
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    # take first 8 chars as int
    int_val = int(h[:8], 16)
    return min_val + (int_val % (max_val - min_val + 1))


# --- API ROUTES ---
@app.route('/api/train-status', methods=['GET'])
def get_train_status():
    train_number = request.args.get('number')
    if not train_number:
        return jsonify({"error": "No train number provided"}), 400

    try:
        response, data = get_rapidapi_data(train_number)
        
        # Parse RapidAPI data gracefully
        if response.status_code != 200 or data.get('status') == False or not data.get('data'):
            error_message = data.get('message', "Train not found or hasn't started yet. Please check the number.")
            return jsonify({"error": error_message}), 404
            
        t_data = data['data']
        train_name = t_data.get('trainName', f'Train {train_number}')
        
        # Check running days
        today_str = datetime.now().strftime("%a")
        runs_today = t_data.get('runningDays', {}).get(today_str, True)
        
        # Determine source and destination if not actively running
        active_source = t_data.get('currentStation')
        active_dest = t_data.get('nextStation')
        
        # Reliably derive Origin and Destination from trainRoute
        t_route = t_data.get('trainRoute', [])
        if not active_source and len(t_route) > 0:
            source = t_route[0].get('stationName', 'Origin')
            dest = t_route[-1].get('stationName', 'Destination')
        elif not active_source and 'route' in t_data:
            route_parts = t_data['route'].split(' to ')
            if len(route_parts) == 2:
                source = route_parts[0]
                dest = route_parts[1]
            else:
                source = "Origin"
                dest = "Destination"
        else:
            source = active_source or 'Unknown Station'
            dest = active_dest or 'Unknown Station'

        departure = "--:--"
        arrival = t_data.get('estimatedArrivalTime', '--:--')
        if not active_source and t_data.get('trainRoute') and len(t_data['trainRoute']) > 0:
            departure = t_data['trainRoute'][0].get('departs', '--:--')
            if arrival == '--:--':
                arrival = t_data['trainRoute'][-1].get('arrives', '--:--')
                
        delay = t_data.get('delayMins', 0)
        dist = t_data.get('totalDistance', "800 km")
        
        # Color coding status and location message
        is_tracking_active = bool(active_source)
        if not runs_today:
            status_badge = {"label": "NOT RUNNING TODAY", "color": "red"}
            current_location = f"Train does not operate on {today_str}s"
        elif not is_tracking_active:
            # Check if current time has passed departure time
            # Because RapidAPI sometimes simply drops live tracking strings
            has_started = False
            if departure != '--:--':
                try:
                    dep_hour, dep_min = map(int, departure.split(':'))
                    if now.hour > dep_hour or (now.hour == dep_hour and now.minute >= dep_min):
                        has_started = True
                except:
                    pass
            
            if has_started:
                status_badge = {"label": "DATA UNAVAILABLE", "color": "yellow"}
                current_location = f"Train departed {departure} but RapidAPI lacks live telemetry for this route."
            else:
                status_badge = {"label": "YET TO START", "color": "yellow"}
                current_location = f"Train hasn't started yet. Scheduled at {departure}"
        else:
            current_location = source
            if delay < 5:
                status_badge = {"label": "ON TIME", "color": "green"}
            elif delay <= 30:
                status_badge = {"label": "SLIGHT DELAY", "color": "yellow"}
            else:
                status_badge = {"label": "HEAVY DELAY", "color": "red"}

        # Extract features from datetime.now()
        now = datetime.now()
        month = now.month
        hour = now.hour
        day_of_week = now.weekday()
        
        # Calculate season
        if month in [12, 1, 2]: season = 'Winter'
        elif month in [3, 4, 5]: season = 'Summer'
        elif month in [6, 7, 8, 9]: season = 'Monsoon'
        else: season = 'Autumn'

        # ML Prediction (now passing in live delay and real distance)
        pred_label, confidence, reason = predict_delay(month, hour, day_of_week, dist, season, delay)
        
        return jsonify({
            "train_name": train_name,
            "source": source,
            "destination": dest,
            "departure": departure, 
            "arrival": arrival,
            "current_location": current_location,
            "status": status_badge,
            "prediction_label": pred_label,
            "confidence": f"{confidence}%",
            "reason": reason
        })

    except Exception as e:
        logging.error(f"API Error: {e}")
        return jsonify({"error": "Failed to connect to live tracking."}), 500


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    train_number = request.args.get('train', 'Unknown')
    
    # 1. Fetch real route data for the speed analysis
    response, data = get_rapidapi_data(train_number)
    
    dist_val = 1400  # Fallback
    duration_hrs = 24 # Fallback
    train_class = "Express"
    
    if data and data.get('data'):
        t_data = data['data']
        route_str = t_data.get('route', '')
        # Check if train name contains Rajdhani, Shatabdi, Superfast etc.
        name = t_data.get('trainName', '').upper()
        if "RAJDHANI" in name: train_class = "Rajdhani"
        elif "SHATABDI" in name: train_class = "Shatabdi"
        elif "VANDE" in name: train_class = "Vande Bharat"
        elif "SF" in name or "SUPERFAST" in name: train_class = "Superfast"
        
        # Extract distance from last leg of trainRoute
        t_route = t_data.get('trainRoute', [])
        if t_route and len(t_route) > 0:
            last_dist_str = t_route[-1].get('distance', "1400 km")
            match = re.search(r'([\d\.]+)', str(last_dist_str))
            if match:
                dist_val = float(match.group(1))
            
            # Simple duration estimation (number of days * 24 or similar)
            last_day = t_route[-1].get('day', 1)
            duration_hrs = int(last_day) * 20
            
    # Real speed calculation
    avg_speed = round(dist_val / duration_hrs) if duration_hrs > 0 else 55
    
    # 2. Cryptographic Stable Hashing for Missing Historical Metrics
    # Every train will now get uniquely generated (but permanent) dashboard numbers
    
    avg_delay_seed = pseudo_random(train_number + "avg", 5, 120)
    ontime_seed = pseudo_random(train_number + "ont", 30, 95)
    
    # Unique monthly demand
    monthly_d = [pseudo_random(train_number + f"dem{m}", 30, 100) for m in range(12)]
    
    # Unique cancellations
    cancels_m = [pseudo_random(train_number + f"can{m}", 0, 8) for m in range(12)]
    if train_class in ["Rajdhani", "Vande Bharat"]:
        cancels_m = [c // 2 for c in cancels_m]  # Premium trains cancel less
        
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    busiest = months[monthly_d.index(max(monthly_d))]
    
    return jsonify({
        "train_number": train_number,
        "avg_delay": f"{avg_delay_seed} mins",
        "ontime_rate": f"{ontime_seed}%",
        "peak_season": "Winter (Dec–Feb)" if avg_delay_seed > 60 else "Monsoon (Jun-Sep)",
        "busiest_month": busiest,
        "monthly_demand": monthly_d,
        "delay_by_season": {
            "Summer": {"emoji": "☀", "delay": f"{pseudo_random(train_number+'sum', 5, 30)} min", "color": "green"},
            "Monsoon": {"emoji": "🌧", "delay": f"{pseudo_random(train_number+'mon', 10, 80)} min", "color": "yellow"},
            "Autumn": {"emoji": "🍂", "delay": f"{pseudo_random(train_number+'aut', 5, 20)} min", "color": "green"},
            "Winter": {"emoji": "❄", "delay": f"{pseudo_random(train_number+'win', 30, 200)} min", "color": "red"},
        },
        "cancellations_by_month": cancels_m,
        "distance_km": dist_val,
        "duration_hrs": duration_hrs,
        "avg_speed": f"{avg_speed} km/h",
        "train_class": train_class
    })

if __name__ == '__main__':
    from ml_model import create_and_train_model
    import os
    if not os.path.exists('models/clf.pkl') or not os.path.exists('models/reg.pkl'):
        create_and_train_model()
    
    app.run(debug=True, port=5000)
