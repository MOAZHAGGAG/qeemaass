# 🚀 Event Registration System - Complete Setup Guide

## 📋 **System Overview**

This system provides automated email notifications for event registrations using:
- **PostgreSQL** with CDC (Change Data Capture)
- **Kafka** for event streaming
- **Debezium** for database change capture
- **Python Email Service** for sending confirmation emails
- **Streamlit Frontend** with registration functionality

## 🛠️ **Prerequisites**

1. **Docker & Docker Compose** installed
2. **PostgreSQL** running (via docker-compose)
3. **Email Account** (Gmail recommended) with App Password
4. **OpenAI API Key** (for AI features)

## 📧 **Email Configuration Setup**

### For Gmail:
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Go to Google Account settings
   - Security → App passwords
   - Generate password for "Mail"
3. Use this app password (not your regular password)

### Environment Variables:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Event Management System
```

## 🚀 **Quick Start**

### 1. Setup Database Schema
```bash
# Apply registration schema
chmod +x setup_registration.sh
./setup_registration.sh
```

### 2. Configure Environment
```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your email credentials
nano .env
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# Start only email service
docker-compose up -d email_service

# View email service logs
docker-compose logs -f email_service
```

### 4. Setup Connectors
```bash
# Wait for services to start (2-3 minutes)
sleep 180

# Setup registration connector
python import_registration_connector.py
```

## 📊 **Database Schema**

### Users Table (Extended)
```sql
- id (Primary Key)
- username (Unique)
- email (Unique, Required for emails)
- full_name
- password
- created_at/updated_at
```

### Event Registrations Table
```sql
- id (Primary Key)
- user_id (Foreign Key → users.id)
- event_id (Foreign Key → events.id)
- registration_date
- status ('registered', 'cancelled', 'waitlist')
- email_sent (Boolean)
- email_sent_at
- notes
```

## 🔄 **How It Works**

1. **User Registration Flow:**
   ```
   User clicks "Register" → Database INSERT → Kafka Message → Email Service → SMTP → User Email
   ```

2. **Change Data Capture:**
   ```
   PostgreSQL → Debezium → Kafka Topic → Email Consumer
   ```

3. **Email Processing:**
   ```
   - Monitors: event_management.public.event_registrations
   - Triggers: On INSERT with status='registered'
   - Sends: Professional HTML confirmation email
   - Updates: email_sent flag in database
   ```

## 🎨 **Frontend Features**

### New Registration UI:
- **Event Cards**: Enhanced display with registration buttons
- **Registration Status**: Shows if user is already registered
- **My Registrations Page**: View and manage registrations
- **Email Integration**: Users get confirmation emails automatically

### Navigation:
- **🤖 AI Chat**: Find events with AI assistance
- **🗓️ My Registrations**: Manage your event registrations

## 🧪 **Testing the System**

### 1. Test Registration Flow
```bash
# 1. Sign up with valid email
# 2. Find events using AI chat
# 3. Click "Register" on an event
# 4. Check email for confirmation
# 5. View registration in "My Registrations"
```

### 2. Monitor Email Service
```bash
# Check email service logs
docker-compose logs email_service

# Check Kafka topics
docker exec -it kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Check database
psql -h localhost -p 5445 -U eventuser -d event_management
SELECT * FROM event_registrations ORDER BY registration_date DESC;
```

### 3. Test Email Delivery
```sql
-- Manually insert a registration to test email
INSERT INTO event_registrations (user_id, event_id, status) 
VALUES (1, 1, 'registered');
```

## 🔧 **Troubleshooting**

### Email Service Not Sending
```bash
# Check email service logs
docker-compose logs email_service

# Common issues:
# 1. Wrong SMTP credentials
# 2. Gmail App Password not set
# 3. Firewall blocking SMTP ports
# 4. Email service not receiving Kafka messages
```

### Kafka/Debezium Issues
```bash
# Check Debezium connector status
curl http://localhost:8083/connectors/registration-connector/status

# Restart connectors
python import_registration_connector.py

# Check topics
docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Database Issues
```bash
# Check if schema was applied
psql -h localhost -p 5445 -U eventuser -d event_management -c "\\dt"

# Reapply schema
psql -h localhost -p 5445 -U eventuser -d event_management -f registration_schema.sql
```

## 📁 **File Structure**

```
├── registration_schema.sql          # Database schema
├── email_service.py                 # Email service (Kafka consumer)
├── Dockerfile.email                 # Email service container
├── requirements-email.txt           # Email service dependencies
├── registration-connector.json      # Debezium connector config
├── import_registration_connector.py # Connector setup script
├── setup_registration.sh            # Setup script
├── .env.example                     # Environment template
├── main.py                          # Updated Streamlit app
└── docker-compose.yml               # Updated with email service
```

## 🎯 **Production Considerations**

### Security:
- [ ] Use strong passwords for database
- [ ] Secure email credentials
- [ ] Enable SSL/TLS for email
- [ ] Implement rate limiting

### Monitoring:
- [ ] Set up log aggregation
- [ ] Monitor email delivery rates
- [ ] Track registration metrics
- [ ] Health checks for services

### Scalability:
- [ ] Use external Kafka cluster
- [ ] Database connection pooling
- [ ] Email service horizontal scaling
- [ ] Load balancing for frontend

## 📧 **Email Template**

The system sends professional HTML emails with:
- ✅ Event confirmation details
- 📅 Date, time, and location
- 📝 Event description
- 👤 Organizer information
- 🎨 Branded styling
- 📱 Mobile-responsive design

## 🎉 **Success Metrics**

After setup, you should see:
- ✅ Users can register for events
- ✅ Registration data in PostgreSQL
- ✅ Kafka messages for registrations
- ✅ Confirmation emails delivered
- ✅ Users can view/manage registrations

## 📞 **Support**

If you encounter issues:
1. Check the logs: `docker-compose logs email_service`
2. Verify email credentials in `.env`
3. Ensure all services are running: `docker-compose ps`
4. Test database connectivity manually

---
*Event Registration System v1.0*  
*Professional email notifications for event management*
