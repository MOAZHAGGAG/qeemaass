# Event Management System - Docker Setup

🚀 **One-command deployment of a complete Event Management System with AI-powered recommendations and real-time notifications.**

## 🌟 Features

- **Event Management**: Create, browse, and manage events
- **AI-Powered Chatbots**: Two intelligent chatbots for event recommendations
- **Real-time Notifications**: Email notifications via Kafka CDC
- **Vector Search**: Weaviate-powered semantic event search
- **Database**: PostgreSQL with sample data and complete schema
- **Microservices**: Fully containerized with Docker Compose

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend Apps │    │   Backend API   │    │  Email Service  │
│  (Streamlit)    │    │   (FastAPI)     │    │   (Kafka CDC)   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
    ┌─────────────────────────────┼─────────────────────────────┐
    │                             │                             │
┌───▼────┐  ┌─────────┐  ┌────────▼────────┐  ┌─────────────┐
│PostgreSQL│  │ Weaviate │  │   Kafka Stack   │  │  Debezium   │
│Database│  │ Vector  │  │ (Zookeeper +    │  │   Connect   │
│        │  │   DB    │  │  Kafka + Schema │  │   (CDC)     │
└────────┘  └─────────┘  └─────────────────┘  └─────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- **Docker** (20.0+)
- **Docker Compose** (1.29+)
- **8GB RAM** (recommended)
- **5GB disk space**

### 2. Clone and Setup

```bash
git clone <your-repo>
cd qeemaass-dev/docker
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your values
nano .env
```

**Required Configuration:**
- `OPENAI_APIKEY`: Your OpenAI API key for AI features
- `SMTP_*`: Email server settings for notifications

### 4. Start Everything

```bash
# One-command startup (recommended)
./start-event-management.sh

# Or manual startup
docker-compose up -d
```

### 5. Access the System

- **Main Frontend**: http://localhost:8501
- **Chatbot SS**: http://localhost:8502  
- **Chatbot SS2**: http://localhost:8503
- **Backend API**: http://localhost:8000
- **Database**: localhost:5445

## 📊 What Gets Automatically Set Up

### ✅ Database Schema
- **Users table** with authentication
- **Events table** with 32+ sample events (Cairo-based)
- **Registrations table** with email tracking
- **Indexes** for performance
- **Triggers** for automatic timestamps
- **Views** for joined data

### ✅ AI & Search
- **Weaviate vector database** with proper schema
- **Event embeddings** for semantic search
- **AI chatbots** powered by OpenAI
- **Recommendation engine**

### ✅ Real-time Pipeline
- **Kafka cluster** with Zookeeper
- **Debezium CDC connectors** for database changes
- **Email notifications** for new registrations
- **Schema registry** for data consistency

### ✅ Microservices
- **Backend API** (FastAPI) with full CRUD
- **Frontend apps** (Streamlit) with different interfaces
- **Email service** for automated notifications
- **Health checks** and monitoring

## 🔧 Management Commands

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f frontend-ss

# Check service status
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v

# Fresh restart (rebuild everything)
./start-event-management.sh --fresh
```

## 🛠️ Manual Setup (if needed)

If the automatic initialization fails, you can run these manually:

```bash
# Initialize database schema
docker exec -i event_management_db psql -U eventuser -d event_management < migrations/init.sql

# Setup Weaviate schema
docker-compose exec master_init python import_weaviate_schema.py

# Setup Debezium connectors
docker-compose exec master_init python import_registration_connector.py
```

## 🔍 Verification

### Database Health
```bash
# Check tables exist
docker exec event_management_db psql -U eventuser -d event_management -c "\\dt"

# Check sample events
docker exec event_management_db psql -U eventuser -d event_management -c "SELECT COUNT(*) FROM events;"
```

### API Health
```bash
curl http://localhost:8000/health
curl http://localhost:8000/events?limit=5
```

### Weaviate Health
```bash
curl http://localhost:8080/v1/.well-known/ready
curl http://localhost:8080/v1/schema
```

### Kafka Health
```bash
docker exec event_management_kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## 📧 Email Configuration

For Gmail (recommended):

1. Enable 2-Factor Authentication
2. Generate an App Password
3. Use these settings in `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Event Management System
```

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check Docker resources
docker system df
docker system prune -f

# Check port conflicts
netstat -tulpn | grep :8501
```

### Database Issues
```bash
# Reset database
docker-compose down postgres
docker volume rm docker_postgres_data
docker-compose up -d postgres
```

### Weaviate Issues
```bash
# Reset Weaviate
docker-compose down weaviate
docker volume rm docker_weaviate_data
docker-compose up -d weaviate
```

### Email Issues
```bash
# Check email service logs
docker-compose logs -f email_service

# Test SMTP settings
docker-compose exec email_service python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email', 'your-password')
print('SMTP connection successful!')
"
```

## 🔒 Security Notes

- Database is only accessible locally (port 5445)
- Services communicate through internal Docker network
- No passwords are stored in plain text
- Email credentials should use app passwords
- Consider using Docker secrets in production

## 📈 Performance Tuning

For better performance on larger datasets:

```yaml
# Add to docker-compose.yml under postgres:
environment:
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
  POSTGRES_WORK_MEM: 64MB
```

## 🆕 Updating

```bash
# Pull latest images
docker-compose pull

# Rebuild with updates
docker-compose build --no-cache

# Restart with fresh images
./start-event-management.sh --fresh
```

## 📞 Support

- Check service logs: `docker-compose logs -f [service]`
- Verify network: `docker network inspect docker_event_network`
- Check resources: `docker stats`
- Database access: `docker exec -it event_management_db psql -U eventuser -d event_management`

---

**🎉 Your Event Management System is now fully automated and ready to use!**
