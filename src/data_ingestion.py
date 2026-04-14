import pandas as pd
import numpy as np
import os
import requests
import json
import logging
from datetime import datetime, timedelta

# Create a logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DataIngestion")

def generate_historical_data(num_records=5000, output_path='../data/raw_train_data.csv'):
    """
    Generates synthetic historical train data for ML modeling since 
    historical APIs are often unavailable or expensive.
    """
    logger.info(f"Generating {num_records} synthetic historical train records...")
    
    np.random.seed(42)
    # Common Indian trains
    trains = [
        {'train_no': '22924', 'type': 'Superfast', 'distance': 1500, 'avg_duration': 24},
        {'train_no': '12951', 'type': 'Rajdhani', 'distance': 1380, 'avg_duration': 16},
        {'train_no': '12004', 'type': 'Shatabdi', 'distance': 450, 'avg_duration': 6},
        {'train_no': '11020', 'type': 'Express', 'distance': 1800, 'avg_duration': 36},
        {'train_no': '12423', 'type': 'Rajdhani', 'distance': 2100, 'avg_duration': 30},
    ]
    
    data = []
    start_date = datetime.now() - timedelta(days=365)
    
    for _ in range(num_records):
        train = np.random.choice(trains)
        
        # Random date within the last year
        random_days = np.random.randint(0, 365)
        departure_date = start_date + timedelta(days=random_days)
        
        # Weather condition
        weather = np.random.choice(['Clear', 'Rainy', 'Foggy', 'Stormy'], p=[0.6, 0.2, 0.15, 0.05])
        
        # Calculate delay based on constraints
        base_delay = np.random.exponential(scale=15) # most are short delays
        if weather == 'Foggy':
            base_delay += np.random.normal(loc=120, scale=30)
        elif weather == 'Rainy':
            base_delay += np.random.normal(loc=30, scale=10)
            
        if train['type'] == 'Rajdhani' or train['type'] == 'Shatabdi':
            base_delay *= 0.5 # Premium trains get prioritized
            
        final_delay_minutes = max(0, int(base_delay))
        
        # Determine if it's considered "Highly Delayed" (> 60 minutes)
        is_delayed = 1 if final_delay_minutes > 60 else 0
        
        data.append({
            'train_no': train['train_no'],
            'train_type': train['type'],
            'distance_km': train['distance'],
            'departure_date': departure_date.strftime('%Y-%m-%d'),
            'day_of_week': departure_date.strftime('%A'),
            'weather_condition': weather,
            'delay_minutes': final_delay_minutes,
            'is_delayed': is_delayed
        })
        
    df = pd.DataFrame(data)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Historical data generated and saved to {output_path}")
    return output_path

def get_live_train_status(train_no, api_key="a26f2545ddmsh885a99bc9eef333p137471jsn8bf922def494"):
    """
    Fetches real-time status of a train from the RapidAPI irctc-insight API.
    """
    url = "https://irctc-insight.p.rapidapi.com/api/v1/train-details"
    
    payload = {"trainNo": str(train_no)}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "irctc-insight.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # If API returns error message (like not subscribed), fallback to mock
        if 'message' in data and 'not subscribed' in data['message'].lower():
            logger.warning("API key not subscribed. Using mock data.")
            return get_mock_live_status(train_no)
            
        return data
    except Exception as e:
        logger.error(f"Error fetching live data: {e}. Falling back to mock data.")
        return get_mock_live_status(train_no)

def get_mock_live_status(train_no):
    """
    Provides mock json data to ensure the Streamlit dashboard 
    functions perfectly during a demo if the API is down or quota exceeded.
    """
    return {
        "status": "success",
        "data": {
            "trainNumber": train_no,
            "trainName": f"MOCK EXPRESS {train_no}",
            "currentStation": "New Delhi (NDLS)",
            "nextStation": "Kanpur Central (CNB)",
            "departed": True,
            "delayMins": np.random.randint(0, 120),
            "distanceCovered": 440,
            "totalDistance": 1400,
            "estimatedArrivalTime": "20:45:00"
        }
    }

if __name__ == "__main__":
    generate_historical_data()
