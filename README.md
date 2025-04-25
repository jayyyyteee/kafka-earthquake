# Kafka Earthquake Data Pipeline

A real-time data pipeline that continuously collects, processes, and visualizes global earthquake data from SeismicPortal.eu.

## Overview

This system establishes a persistent connection to seismic data sources and builds a **live, continuously-growing database** of global earthquake events. As soon as you start the pipeline, it begins capturing earthquake data in real-time, allowing you to:

- Build a comprehensive database of global seismic activity
- Visualize earthquakes on an interactive map
- Filter events by magnitude and time period
- Monitor seismic trends with real-time statistics

## Architecture

This project implements a modern data pipeline with the following components:

1. **Kafka Producer**: Maintains a WebSocket connection to SeismicPortal.eu and publishes real-time earthquake data to a Kafka topic
2. **Kafka**: Acts as a resilient message buffer between data collection and processing
3. **Kafka Consumer**: Processes incoming earthquake data and stores it in PostgreSQL
4. **PostgreSQL Database**: Accumulates all earthquake records as they occur globally
5. **Streamlit Dashboard**: Provides interactive visualization of the continuously updating earthquake database

## Prerequisites

- Docker and Docker Compose

## Quick Start

1. Clone this repository
2. Create a logs directory: `mkdir -p logs`
3. Start the entire system with Docker Compose:

```bash
docker compose up --build
```

This will start:
- Zookeeper
- Kafka
- PostgreSQL database
- Earthquake data producer
- Earthquake data consumer
- Streamlit dashboard

4. Access the live dashboard at [http://localhost:8501](http://localhost:8501)

**Note**: Your earthquake database will start empty and grow over time as new seismic events occur. The system requires no manual data loading - it automatically captures earthquake data as it's published by seismic monitoring stations.

## Monitoring

### View the Dashboard

The most user-friendly way to monitor the system is through the Streamlit dashboard at [http://localhost:8501](http://localhost:8501), which provides:
- Real-time map visualization
- Data filtering capabilities
- Earthquake statistics
- Tabular data views

### View logs

To view the producer logs:
```bash
docker compose logs -f earthquake-producer
```

To view the consumer logs:
```bash
docker compose logs -f earthquake-consumer
```

### Check data in PostgreSQL

Connect to the PostgreSQL database:
```bash
docker compose exec postgres psql -U earthquake -d earthquakedb
```

Query recent earthquakes:
```sql
SELECT unid, magnitude, time, region FROM earthquakes ORDER BY time DESC LIMIT 10;
```

Query significant earthquakes:
```sql
SELECT unid, magnitude, time, region FROM earthquakes WHERE magnitude >= 5.0 ORDER BY time DESC;
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
docker compose down
``` 