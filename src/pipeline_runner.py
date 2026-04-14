import logging
import time

# Import pipeline steps
from data_ingestion import generate_historical_data
from preprocessing import clean_and_load_data
from model_training import train_and_evaluate

logging.basicConfig(level=logging.INFO, format='%(asctime)s -  %(message)s')
logger = logging.getLogger("PipelineRunner")

def run_pipeline():
    """
    Simulates a Data Engineering workflow / ETL pipeline.
    In a real-world scenario, this might be managed by Apache Airflow or Luigi.
    """
    logger.info("====================================")
    logger.info("STARTING DATA ENGINEERING PIPELINE")
    logger.info("====================================")
    
    start_time = time.time()
    
    # Step 1: Data Extraction / Generation
    logger.info("[STEP 1/3]: Data Ingestion Workflow")
    raw_csv = generate_historical_data(num_records=5000, output_path='data/raw_train_data.csv')
    
    # Step 2: Data Transformation & Loading
    logger.info("[STEP 2/3]: Data Cleansing and Warehousing")
    db_path = clean_and_load_data(input_csv=raw_csv, db_path='data/train_data.db')
    
    # Step 3: Model Training
    logger.info("[STEP 3/3]: Triggering Machine Learning Model Retrain")
    if db_path:
        train_and_evaluate(db_path=db_path, model_path='models/model.pkl')
    else:
        logger.error("Pipeline failed at Step 2. Aborting Step 3.")
        
    execution_time = time.time() - start_time
    logger.info("====================================")
    logger.info(f"PIPELINE COMPLETED in {execution_time:.2f} seconds.")
    logger.info("====================================")

if __name__ == "__main__":
    run_pipeline()
