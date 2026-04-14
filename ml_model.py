import pandas as pd
import numpy as np
import pickle
import os
import re
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def create_and_train_model():
    """
    Trains TWO robust machine learning models on simulated Indian Railways data.
    1. Classifier: Predicts Delay status (Low Risk, Moderate Risk, High Risk)
    2. Regressor: Predicts actual Estimated Delay Time in Minutes
    Features: month, hour, day_of_week, route_distance_km, season, live_delay_mins
    """
    print("Generating synthetic real-world Indian Railways data...")
    # Generate 5000 rows
    np.random.seed(42)
    n_samples = 8000
    
    # 1. month: 1-12
    months = np.random.randint(1, 13, n_samples)
    # 2. hour: 0-23
    hours = np.random.randint(0, 24, n_samples)
    # 3. day_of_week: 0 (Mon) to 6 (Sun)
    day_of_week = np.random.randint(0, 7, n_samples)
    # 4. route_distance_km: 100 to 3000
    dist = np.random.randint(100, 3000, n_samples)
    # 5. live delay (simulating what the train is currently doing)
    live_delay = np.random.exponential(scale=15, size=n_samples).astype(int)
    
    # 6. season derived from month
    def get_season(m):
        if m in [12, 1, 2]: return 'Winter'
        elif m in [3, 4, 5]: return 'Summer'
        elif m in [6, 7, 8, 9]: return 'Monsoon'
        else: return 'Autumn'
    
    seasons = [get_season(m) for m in months]
    
    # Mathematical Modeling of true Indian Railway Risk 
    target_delays = []
    labels = []
    
    for i in range(n_samples):
        base_delay = live_delay[i]
        
        # Heavy delays in winter nights (Fog)
        if seasons[i] == 'Winter' and (hours[i] >= 22 or hours[i] <= 7):
            base_delay += np.random.randint(60, 240)
            
        # Heavy delays in Monsoon due to speed restrictions
        if seasons[i] == 'Monsoon':
            base_delay += np.random.randint(30, 180)
            
        # Distances over 1500km naturally accumulate more delay
        if dist[i] > 1500:
            base_delay += np.random.randint(20, 100)
            
        # Weekend congestion at hubs
        if day_of_week[i] >= 5:
            base_delay += np.random.randint(10, 40)
            
        # Classify labels based on final total minutes of delay expected
        if base_delay > 120:
            labels.append("High Risk ✗")
        elif base_delay > 45:
            labels.append("Moderate Risk ⚠")
        else:
            labels.append("Low Risk ✓")
            
        target_delays.append(base_delay)
            
    df = pd.DataFrame({
        'month': months,
        'hour': hours,
        'day_of_week': day_of_week,
        'route_distance_km': dist,
        'season': seasons,
        'live_delay': live_delay,
        'risk_label': labels,
        'target_delay_mins': target_delays
    })
    
    print("Training ML Pipelines...")
    X = df.drop(['risk_label', 'target_delay_mins'], axis=1)
    
    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), ['month', 'hour', 'day_of_week', 'route_distance_km', 'live_delay']),
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['season'])
    ])
    
    # Train Classifier (Label)
    clf_pipeline = Pipeline([
        ('preproc', preprocessor),
        ('clf', RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10))
    ])
    clf_pipeline.fit(X, df['risk_label'])
    
    # Train Regressor (Minutes)
    reg_pipeline = Pipeline([
        ('preproc', preprocessor),
        ('reg', RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10))
    ])
    reg_pipeline.fit(X, df['target_delay_mins'])
    
    # Save Models
    os.makedirs('models', exist_ok=True)
    with open('models/clf.pkl', 'wb') as f: pickle.dump(clf_pipeline, f)
    with open('models/reg.pkl', 'wb') as f: pickle.dump(reg_pipeline, f)
        
    print("Models saved successfully.")
    return clf_pipeline, reg_pipeline

def parse_distance(dist_str):
    """Safely extracts float from '1400 km' etc."""
    if isinstance(dist_str, (int, float)): return float(dist_str)
    if not dist_str: return 0.0
    match = re.search(r'([\d\.]+)', str(dist_str))
    return float(match.group(1)) if match else 0.0

def predict_delay(month, hour, day_of_week, distance_km, season, live_delay):
    """
    Inference function for Flask app. 
    """
    if not os.path.exists('models/clf.pkl') or not os.path.exists('models/reg.pkl'):
        create_and_train_model()
        
    with open('models/clf.pkl', 'rb') as f: clf = pickle.load(f)
    with open('models/reg.pkl', 'rb') as f: reg = pickle.load(f)
        
    dist = parse_distance(distance_km)
        
    input_data = pd.DataFrame([{
        'month': month,
        'hour': hour,
        'day_of_week': day_of_week,
        'route_distance_km': dist,
        'season': season,
        'live_delay': float(live_delay)
    }])
    
    # Classifier Output
    pred_label = clf.predict(input_data)[0]
    idx = list(clf.classes_).index(pred_label)
    confidence = int(clf.predict_proba(input_data)[0][idx] * 100)
    
    # Regressor Output
    est_mins = int(reg.predict(input_data)[0])
    
    # Format label with time requirement
    if pred_label != "Low Risk ✓":
        pred_label = f"{pred_label} (+{est_mins} mins)"
    else:
        # If it's low risk but has a small delay
        if est_mins > 15:
            pred_label = f"{pred_label} (+{est_mins} mins)"
    
    # Plain English reasoning
    reason = "Normal operating conditions."
    if season == 'Winter': reason = "Winter fog season notoriously causes 2-3 hour delays on this route."
    elif season == 'Monsoon': reason = "Monsoon weather often leads to speed restrictions and prolonged journey times."
    elif dist > 1500: reason = "Long-haul routes naturally accumulating varying delays over time."
    if live_delay > 60: reason = f"Train is already running late by {live_delay} mins. Delays are expected to compound downstream."
    
    return pred_label, confidence, reason

if __name__ == "__main__":
    create_and_train_model()
