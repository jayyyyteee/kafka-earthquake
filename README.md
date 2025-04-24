# Kafka Earthquake Data Pipeline

A real-time data pipeline for ingesting earthquake data from SeismicPortal.eu using Apache Kafka.

## Architecture

This project implements a simple data pipeline with the following components:

1. **Kafka Producer**: Fetches real-time earthquake data from SeismicPortal.eu and publishes it to a Kafka topic
2. **Kafka Consumer**: Subscribes to the Kafka topic and processes the earthquake data
3. **PostgreSQL Database**: Stores the processed earthquake data

## Prerequisites

- Docker and Docker Compose

## Quick Start

1. Clone this repository
2. Create a logs directory: `mkdir -p logs`
3. Start the entire system with Docker Compose:

```bash
docker-compose up -d
```

This will start:
- Zookeeper
- Kafka
- PostgreSQL database
- Earthquake data producer
- Earthquake data consumer

## Monitoring

### View logs

To view the producer logs:
```bash
docker-compose logs -f earthquake-producer
```

To view the consumer logs:
```bash
docker-compose logs -f earthquake-consumer
```

### Check data in PostgreSQL

Connect to the PostgreSQL database:
```bash
docker-compose exec postgres psql -U earthquake -d earthquakedb
```

Query recent earthquakes:
```sql
SELECT id, magnitude, time, place FROM earthquakes ORDER BY time DESC LIMIT 10;
```

Query significant earthquakes:
```sql
SELECT id, magnitude, time, place FROM earthquakes WHERE magnitude >= 5.0 ORDER BY time DESC;
```

## Configuration

The pipeline is configured with the following components:

- **Producer**: Maintains a continuous WebSocket connection to SeismicPortal.eu, receiving earthquake data in real-time as events occur
- **Kafka**: Acts as a message buffer, decoupling data production from consumption
- **Consumer**: Processes all incoming earthquake messages from Kafka and stores them in PostgreSQL
- **Dashboard**: Provides a visualization interface with customizable filters for magnitude and time range

The system collects all earthquake data regardless of magnitude. The Streamlit dashboard allows filtering by magnitude and time period at display time.

You can modify these settings in the `producer_websocket.py`, `consumer.py`, and `earthquake_dashboard.py` files.

## Architecture Details

### Producer (`producer_websocket.py`)
- Establishes a persistent WebSocket connection to SeismicPortal.eu
- Receives earthquake data in real-time as events occur
- Tracks which earthquakes have already been processed
- Publishes earthquakes to the Kafka "earthquakes" topic

### Consumer (`consumer.py`)
- Subscribes to the Kafka "earthquakes" topic
- Processes incoming earthquake data
- Stores earthquake information in the PostgreSQL database

### Database Utilities (`db_utils.py`)
- Handles connections to PostgreSQL
- Creates necessary database tables
- Provides functions for storing and retrieving earthquake data

### Dashboard (`earthquake_dashboard.py`)
- Creates an interactive Streamlit visualization
- Provides filtering by magnitude and time period
- Displays earthquakes on an interactive map
- Shows statistics and tabular data

## Stopping the Pipeline

```bash
docker-compose down
```