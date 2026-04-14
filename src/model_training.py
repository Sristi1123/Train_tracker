import sqlite3
import pandas as pd
import logging
import pickle
import os
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ModelTraining")

def train_and_evaluate(db_path='../data/train_data.db', model_path='../models/model.pkl'):
    """
    Trains ML models to predict if a train will be delayed.
    """
    logger.info(f"Connecting to DB: {db_path}")
    if not os.path.exists(db_path):
        logger.error("Database not found. Please run preprocessing first.")
        return
        
    conn = sqlite3.connect(db_path)
    df = pd.read_sql('SELECT * FROM historical_delays', conn)
    conn.close()
    
    logger.info("Preparing data for modeling...")
    
    # Features and Target
    # We want to predict 'is_delayed' (Classification)
    features = ['train_type', 'distance_km', 'weather_condition', 'is_weekend', 'month']
    X = df[features]
    y = df['is_delayed']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Preprocessing Pipeline
    # Numeric features
    numeric_features = ['distance_km', 'month']
    numeric_transformer = StandardScaler()
    
    # Categorical features
    categorical_features = ['train_type', 'weather_condition', 'is_weekend']
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    # Define models
    models = {
        'Logistic Regression': Pipeline(steps=[('preprocessor', preprocessor),
                                              ('classifier', LogisticRegression(max_iter=1000))]),
        'Random Forest': Pipeline(steps=[('preprocessor', preprocessor),
                                        ('classifier', RandomForestClassifier(random_state=42))])
    }
    
    best_model = None
    best_acc = 0
    best_name = ""
    
    logger.info("Training models to compare performance...")
    for name, pipeline in models.items():
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        logger.info(f"{name} Accuracy: {acc:.4f}")
        
        if acc > best_acc:
            best_acc = acc
            best_model = pipeline
            best_name = name
            
    logger.info(f"Best model selected: {best_name} with Accuracy {best_acc:.4f}")
    logger.info("\nClassification Report:\n" + classification_report(y_test, best_model.predict(X_test)))
    
    # Hyperparameter Tuning for the Best Model (simplified for demo)
    if best_name == 'Random Forest':
        logger.info("Performing Hyperparameter Tuning on Random Forest...")
        param_grid = {
            'classifier__n_estimators': [50, 100],
            'classifier__max_depth': [None, 10, 20]
        }
        grid_search = GridSearchCV(best_model, param_grid, cv=3, scoring='accuracy')
        grid_search.fit(X_train, y_train)
        logger.info(f"Best parameters found: {grid_search.best_params_}")
        final_model = grid_search.best_estimator_
    else:
        final_model = best_model
        
    # Save the model
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(final_model, f)
    
    logger.info(f"Model saved to {model_path}")
    return model_path

if __name__ == "__main__":
    train_and_evaluate()
