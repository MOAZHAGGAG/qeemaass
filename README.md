# Event Management App

This is a simple event management system built with Python, FastAPI, Streamlit, and PostgreSQL. It allows you to create, view, update, and delete events, as well as manage event categories.

## Features
- Add, view, update, and delete events
- Manage event categories (add new categories, select from existing)
- Simple web interface using Streamlit
- REST API backend using FastAPI
- PostgreSQL database for persistent storage
- Dockerized for easy setup and deployment

## Getting Started

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ (for local development)

### Setup
1. Clone the repository:
   ```sh
git clone https://github.com/MOAZHAGGAG/event-management-app.git
cd event-management-app
```

---

## Data Streaming Setup: Kafka, Debezium, and PostgreSQL

This section explains how to set up the environment, configure Kafka and Debezium, and stream data from PostgreSQL to Kafka topics using Docker Compose.

### 1. Docker Compose Configuration
- The `docker-compose.yml` file is updated to:
   - Set up the network.
   - Ensure Kafka and its broker are running.

### 2. Start the Environment
Run the following command to start all services in detached mode:
```bash
docker-compose up -d
```

### 3. Verify Kafka Topics
Check that Kafka is running and list available topics:
```bash
docker exec -it event_management_kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### 4. Enable WAL Logical Replication in PostgreSQL
Edit the `postgresql.conf` file and set:
```
wal_level = logical
```
This enables logical replication required for Debezium.

### 5. Start Debezium Connector
- The Debezium connector runs in a container named `event_management_debezium` on port 8090.
- The connector configuration is written in `postgres-connector.json`.

### 6. Register the Connector via REST API
Upload the connector configuration using:
```bash
curl -X POST -H "Content-Type: application/json" --data @postgres-connector.json http://localhost:8090/connectors
```

### 7. Check Connector Status
Verify the connector is running:
```bash
curl http://localhost:8090/connectors/postgres-connector/status
```
Expected output should include:
```
"state":"RUNNING"
```

### 8. Kafka Topic Creation
The connector automatically creates a topic named:
```
postgres.public.events
```

### 9. View Data in Kafka Topic
To see the data streamed to the topic, run:
```bash
docker exec -it event_management_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic postgres.public.events --from-beginning --property print.key=true --property key.separator=" | " --property print.timestamp=true
```

---

For more details, refer to the configuration files in the repository.
2. Build and start the app using Docker Compose:
   ```sh
docker-compose up --build
```
3. Access the frontend:
   - Open your browser and go to `http://localhost:8501`
4. Access the backend API:
   - Go to `http://localhost:8000/docs` for API documentation

### Database Access
- The PostgreSQL database is exposed on port 5432 (or 5444 for locals such as DBeaver)
- Default credentials:
  - Database: `event_management`
  - User: `eventuser`
  - Password: `eventpass123`

## Project Structure
```
backend/        # FastAPI backend
frontend/       # Streamlit frontend
init.sql        # Database initialization script
Dockerfile.*    # Docker build files
requirements*.txt # Python dependencies
```

## How to Contribute
- Fork the repo and create a pull request
- For questions or issues, open an issue on GitHub

---
Made by Moaz Haggag
