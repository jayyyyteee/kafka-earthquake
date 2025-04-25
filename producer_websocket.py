#!/usr/bin/env python3
"""
Earthquake data ingestion pipeline
WebSocket → Kafka producer for real-time seismic data
"""

import json
import logging
import os
import time
from kafka import KafkaProducer
from tornado.websocket import websocket_connect
from tornado.ioloop import IOLoop
from tornado import gen

# Configuration
WEBSOCKET_URI = 'wss://www.seismicportal.eu/standing_order/websocket'
PING_INTERVAL = 15
KAFKA_TOPIC = 'earthquakes'
KAFKA_BOOTSTRAP_SERVERS = ['kafka:29092']
MAX_CACHE_SIZE = 1000

# Setup logging
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'producer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('earthquake-producer')

# Global state
producer = None
processed_earthquakes = set()

def create_kafka_producer():
    """Establish connection to Kafka"""
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        retries=5
    )
    return producer

@gen.coroutine
def process_earthquake(message):
    """Extract key earthquake data and send to Kafka"""
    global processed_earthquakes
    
    data = json.loads(message)
    
    if 'data' not in data or 'properties' not in data['data']:
        return
        
    properties = data['data']['properties']
    action = data.get('action', 'unknown')
    
    # Extract earthquake ID
    unid = properties.get('unid')
    if not unid or unid in processed_earthquakes:
        return
        
    # Extract coordinates
    coords = data['data'].get('geometry', {}).get('coordinates', [None, None, None])
    lon, lat, depth = coords if len(coords) >= 3 else coords + [None] * (3 - len(coords))
    
    # Core earthquake properties
    mag = properties.get('mag')
    time_str = properties.get('time')
    region = properties.get('flynn_region')
    depth = depth or properties.get('depth')
    
    # Track this earthquake to avoid duplicates
    processed_earthquakes.add(unid)
    
    # Log the extraction
    logger.info(f"EXTRACTED | {action:6} | {unid} | mag:{mag} | region:{region}")
    
    # Create optimized payload with just the key fields
    earthquake_data = {
        'unid': unid,
        'time': time_str,
        'mag': mag,
        'region': region,
        'lat': lat,
        'lon': lon,
        'depth': depth,
        'action': action,
        'processed_ts': time.time()
    }
    
    # Send to Kafka
    producer.send(KAFKA_TOPIC, earthquake_data)
    producer.flush()
    logger.info(f"SENT TO KAFKA | {unid}")
    
    # Maintain cache size
    if len(processed_earthquakes) > MAX_CACHE_SIZE:
        processed_earthquakes = set(list(processed_earthquakes)[-int(MAX_CACHE_SIZE/2):])

@gen.coroutine
def listen_to_websocket(ws):
    """Process messages from the WebSocket"""
    while True:
        msg = yield ws.read_message()
        if msg is None:
            logger.info("WebSocket connection closed")
            break
        
        yield process_earthquake(msg)

@gen.coroutine
def maintain_connection():
    """Maintain persistent WebSocket connection"""
    while True:
        logger.info(f"Opening WebSocket connection to data source")
        ws = yield websocket_connect(WEBSOCKET_URI, ping_interval=PING_INTERVAL)
        logger.info("WebSocket connection established")
        
        yield listen_to_websocket(ws)
        
        logger.info("Reconnecting in 15 seconds...")
        yield gen.sleep(15)

if __name__ == "__main__":
    logger.info("Starting earthquake data ingestion pipeline")
    logger.info("Waiting for Kafka to be fully ready...")
    time.sleep(5)
    # Initialize Kafka producer
    producer = create_kafka_producer()
    logger.info("Kafka producer initialized")
    
    # Start WebSocket client
    ioloop = IOLoop.current()
    ioloop.add_callback(maintain_connection)
    ioloop.start()
