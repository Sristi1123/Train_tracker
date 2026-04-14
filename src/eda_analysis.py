import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("EDA")

def get_data_from_db(db_path='../data/train_data.db'):
    if not os.path.exists(db_path):
        return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM historical_delays", conn)
    conn.close()
    return df

def plot_delay_by_train_type(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    if not df.empty:
        sns.boxplot(data=df, x='train_type', y='delay_minutes', ax=ax, palette='Set2')
        ax.set_title('Delay Distribution by Train Type')
        ax.set_xlabel('Train Type')
        ax.set_ylabel('Delay in Minutes')
    return fig

def plot_delay_by_weather(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    if not df.empty:
        # Calculate delay chance by weather
        delay_rates = df.groupby('weather_condition')['is_delayed'].mean().reset_index()
        sns.barplot(data=delay_rates, x='weather_condition', y='is_delayed', ax=ax, palette='Blues_d')
        ax.set_title('Probability of Severe Delay by Weather Condition')
        ax.set_ylabel('Probability')
        ax.set_xlabel('Weather Condition')
    return fig

def plot_distance_vs_delay(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    if not df.empty:
        sns.scatterplot(data=df, x='distance_km', y='delay_minutes', hue='is_delayed', alpha=0.5, ax=ax)
        ax.set_title('Route Distance vs Delay Minutes')
    return fig

if __name__ == "__main__":
    df = get_data_from_db()
    if not df.empty:
        f1 = plot_delay_by_train_type(df)
        plt.show()
