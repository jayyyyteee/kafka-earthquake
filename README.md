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

The pipeline is configured to:
- Fetch earthquake data every minute
- Process earthquakes with magnitude >= 1.0
- Store all earthquake data in PostgreSQL

You can modify these settings in the `producer.py` and `consumer.py` files.

## Architecture Details

### Producer (`producer.py`)
- Polls the SeismicPortal.eu API every minute
- Tracks which earthquakes have already been processed
- Publishes new earthquakes to the Kafka "earthquakes" topic

### Consumer (`consumer.py`)
- Subscribes to the Kafka "earthquakes" topic
- Processes incoming earthquake data
- Stores earthquake information in the PostgreSQL database

### Database Utilities (`db_utils.py`)
- Handles connections to PostgreSQL
- Creates necessary database tables
- Provides functions for storing and retrieving earthquake data

## Stopping the Pipeline

To stop all services:
```bash
docker-compose down
```

To stop and remove all data (including PostgreSQL volumes):
```bash
docker-compose down -v
``` 