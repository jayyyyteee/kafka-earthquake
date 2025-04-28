#!/usr/bin/env python3
"""
Earthquake data ingestion pipeline
Kafka → PostgreSQL staging loader
"""

import json
import logging
import os
import time
from kafka import KafkaConsumer
from db_utils import initialize_database, save_earthquake

# Ensure logs directory exists
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configuration
KAFKA_TOPIC = 'earthquakes'
KAFKA_BOOTSTRAP_SERVERS = ['kafka:29092']
CONSUMER_GROUP = 'earthquake-loader'

os.environ['DB_HOST'] = 'postgres'
os.environ['DB_NAME'] = 'earthquakedb'
os.environ['DB_USER'] = 'earthquake'
os.environ['DB_PASS'] = 'quakedata'

# Setup logging with file handler
log_file_path = os.path.join(logs_dir, 'consumer.log')

# Create handlers with immediate flush
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Get logger
logger = logging.getLogger('earthquake-loader')
logger.setLevel(logging.INFO)

# Clear any existing handlers
if logger.handlers:
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def flush_logs():
    """Force flush all log handlers"""
    for handler in logger.handlers:
        handler.flush()

def create_kafka_consumer():
    """Establish Kafka connection"""
    logger.info("Attempting to connect to Kafka...")
    flush_logs()
    
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    logger.info(f"Kafka connection established to topic: {KAFKA_TOPIC}")
    flush_logs()
    return consumer

def process_earthquake(earthquake_data):
    """Load earthquake record to PostgreSQL staging table"""
    unid = earthquake_data.get('unid', 'unknown')
    magnitude = earthquake_data.get('mag', 0)
    region = earthquake_data.get('region', 'unknown')
    logger.info(f"Processing earthquake - ID: {unid}, Magnitude: {magnitude}, Region: {region}")
    
    # Save to database
    if save_earthquake(earthquake_data):
        logger.info(f"LOADED | {unid} | mag:{magnitude} | region:{region}")
        flush_logs()
        return True
    else:
        logger.warning(f"LOAD FAILED | {unid}")
        flush_logs()
        return False

def run_pipeline():
    """Main data loading pipeline"""
    logger.info("Initializing database schema...")
    initialize_database()
    flush_logs()
    
    # Connect to Kafka
    logger.info("Connecting to Kafka...")
    consumer = create_kafka_consumer()
    
    # Start data loading
    logger.info("Starting data ingestion...")
    message_count = 0
    error_count = 0
    flush_logs()
    
    for message in consumer:
        earthquake_data = message.value
        success = process_earthquake(earthquake_data)
        
        # Count successes and failures
        message_count += 1
        if not success:
            error_count += 1
        
        # Log progress periodically
        if message_count % 100 == 0:
            logger.info(f"Progress: {message_count} messages processed, {error_count} errors")
            flush_logs()

if __name__ == "__main__":
    logger.info("Starting earthquake data loading pipeline")
    logger.info(f"Using database: {os.environ.get('DB_NAME')} on {os.environ.get('DB_HOST')} as user {os.environ.get('DB_USER')}")
    logger.info("Waiting for services to be fully ready...")
    flush_logs()
    
    time.sleep(5)
    run_pipeline() 