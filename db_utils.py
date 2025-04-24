#!/usr/bin/env python3
"""
Database utilities for earthquake data pipeline
Handles PostgreSQL connection and data loading
"""

import logging
import os
import time
import psycopg2
from psycopg2.extras import Json

# Setup logging
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'db_utils.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('db-utils')

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'earthquakedb')  
DB_USER = os.environ.get('DB_USER', 'earthquake')    
DB_PASS = os.environ.get('DB_PASS', 'quakedata')    

def get_db_connection(max_retries=5, retry_delay=5):
    """Establish connection to PostgreSQL with retry logic"""
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            return conn
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise ConnectionError(f"Failed to connect to database after {max_retries} attempts")

def initialize_database():
    """Create earthquakes table if it doesn't exist"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create earthquakes table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS earthquakes (
            id SERIAL PRIMARY KEY,
            unid VARCHAR(50) UNIQUE,
            time TIMESTAMP WITHOUT TIME ZONE,
            region VARCHAR(255),
            latitude FLOAT,
            longitude FLOAT,
            depth FLOAT,
            magnitude FLOAT,
            action VARCHAR(10),
            raw_data JSONB,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_earthquakes_unid ON earthquakes(unid);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_earthquakes_time ON earthquakes(time);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_earthquakes_magnitude ON earthquakes(magnitude);")
        
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def save_earthquake(earthquake_data):
    """Save earthquake data to PostgreSQL"""
    try:
        # Extract required fields
        unid = earthquake_data.get('unid')
        if not unid:
            return False
            
        # Extract other fields
        event_time = earthquake_data.get('time')
        region = earthquake_data.get('region', '')
        latitude = earthquake_data.get('lat')
        longitude = earthquake_data.get('lon')
        depth = earthquake_data.get('depth')
        magnitude = earthquake_data.get('mag')
        action = earthquake_data.get('action', 'create')
        
        # Connect and insert/update
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if action == 'delete':
            cursor.execute("DELETE FROM earthquakes WHERE unid = %s", (unid,))
        else:
            cursor.execute(
                """
                INSERT INTO earthquakes 
                (unid, time, region, latitude, longitude, depth, magnitude, action, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (unid) 
                DO UPDATE SET 
                    time = EXCLUDED.time,
                    region = EXCLUDED.region,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    depth = EXCLUDED.depth,
                    magnitude = EXCLUDED.magnitude,
                    action = EXCLUDED.action,
                    raw_data = EXCLUDED.raw_data,
                    created_at = CURRENT_TIMESTAMP
                """,
                (
                    unid, 
                    event_time, 
                    region, 
                    latitude, 
                    longitude, 
                    depth, 
                    magnitude,
                    action,
                    Json(earthquake_data)
                )
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception:
        return False 