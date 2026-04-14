import pandas as pd
import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Preprocessing")

def clean_and_load_data(input_csv='../data/raw_train_data.csv', db_path='../data/train_data.db'):
    """
    Cleans raw data and loads into a SQLite Data Warehouse layout.
    """
    logger.info(f"Loading raw data from {input_csv}...")
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        logger.error(f"File {input_csv} not found.")
        return None
        
    # 1. Data Cleaning
    logger.info("Cleaning data (handling missing values, outliers)...")
    # Drop completely empty rows if any
    df.dropna(how='all', inplace=True)
    
    # Cap excessive outliers in delay_minutes (e.g., above 1440 mins / 24 hours)
    df.loc[df['delay_minutes'] > 1440, 'delay_minutes'] = 1440
    
    # 2. Feature Engineering
    logger.info("Engineering new features...")
    df['departure_date'] = pd.to_datetime(df['departure_date'])
    df['month'] = df['departure_date'].dt.month
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x in ['Saturday', 'Sunday'] else 0)
    
    # 3. Categorical Encoding (One-hot encoding for ML readiness, though we can do it in the ml pipeline too)
    # We'll save the cleaned raw-ish dataframe to SQL, and let ML script do the encoding to keep the DB readable.
    
    # 4. Load to SQLite
    logger.info(f"Loading data into SQLite Database at {db_path}...")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    
    # Write to a table named 'historical_delays'
    df.to_sql('historical_delays', conn, if_exists='replace', index=False)
    
    # Log some stats
    count = pd.read_sql('SELECT count(*) FROM historical_delays', conn).iloc[0,0]
    logger.info(f"Successfully inserted {count} rows into historical_delays table.")
    
    conn.close()
    return db_path

if __name__ == "__main__":
    clean_and_load_data()
