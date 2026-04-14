from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import pickle
import pandas as pd
import logging

# Ensure src directory is in path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from data_ingestion import get_live_train_status

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend to communicate easily

# Set up simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backend")

# Load our DE model from disk
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'model.pkl')
try:
    with open(MODEL_PATH, 'rb') as f:
        ml_model = pickle.load(f)
    logger.info("ML Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    ml_model = None

@app.route('/api/track', methods=['GET'])
def track_train():
    train_no = request.args.get('train_no', '22924')
    
    # 1. Fetch live data from RapidAPI
    logger.info(f"Fetching live data for: {train_no}")
    live_status = get_live_train_status(train_no)
    
    # 2. Run background ML Prediction
    # For a real scenario, we'd use the train's actual route details. 
    # Here we simulate feature extraction from the live API response.
    prediction_tag = "UNKNOWN"
    prediction_confidence = 0
    prediction_message = ""
    
    if ml_model and live_status.get('status') == 'success':
        data = live_status['data']
        # Extract/Mock features required by our model: 
        # ['train_type', 'distance_km', 'weather_condition', 'is_weekend', 'month']
        
        # Simple heuristic to derive train_type from name
        train_name = data.get('trainName', 'EXPRESS').upper()
        if 'RAJDHANI' in train_name: t_type = 'Rajdhani'
        elif 'SHATABDI' in train_name: t_type = 'Shatabdi'
        elif 'SUPERFAST' in train_name: t_type = 'Superfast'
        else: t_type = 'Express'
        
        input_features = pd.DataFrame([{
            "train_type": t_type,
            "distance_km": data.get('totalDistance', 1500),
            "weather_condition": "Clear", # simplified
            "month": 4, # current month
            "is_weekend": 0 # weekday
        }])
        
        try:
            pred = ml_model.predict(input_features)[0]
            prob = ml_model.predict_proba(input_features)[0]
            
            if pred == 1:
                prediction_tag = "DELAYS EXPECTED"
                prediction_confidence = int(prob[1] * 100)
                prediction_message = "Historical pipeline flags a high risk of delays on this route."
            else:
                prediction_tag = "ON TIME"
                prediction_confidence = int(prob[0] * 100)
                prediction_message = "Model predicts minimal disruptions."
                
        except Exception as e:
            logger.error(f"Prediction failed: {e}")

    # Combine response
    response_data = {
        "live_api": live_status,
        "prediction": {
            "tag": prediction_tag,
            "confidence": prediction_confidence,
            "message": prediction_message
        }
    }
    
    return jsonify(response_data)

if __name__ == '__main__':
    # Run the Flask API server
    logger.info("Starting API Server on port 5000")
    app.run(debug=True, port=5000)
