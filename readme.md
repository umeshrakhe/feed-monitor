# Feed Monitoring Framework - Setup Guide

## Project Structure
```
feed-monitor/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── config/
│   │   └── feeds.yaml         # Feed configurations
│   ├── models/
│   │   ├── __init__.py
│   │   ├── feed_config.py     # Data models
│   │   └── database.py        # Database connections
│   ├── services/
│   │   ├── __init__.py
│   │   ├── feed_monitor.py    # Core monitoring logic
│   │   ├── alerting.py        # Alert services
│   │   └── scheduler.py       # Job scheduling
│   └── utils/
│       ├── __init__.py
│       ├── database_utils.py  # DB utilities
│       └── date_utils.py      # Date/time utilities
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── FeedGrid.jsx
│   │   │   └── StatusLegend.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── utils/
│   │   │   └── dateUtils.js
│   │   └── App.jsx
│   ├── package.json
│   └── public/
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── scripts/
│   ├── setup_database.py
│   ├── migrate_data.py
│   └── test_connections.py
└── README.md
```

## Quick Start

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create config directory
mkdir -p config

# Copy the feeds.yaml configuration file to config/
# Update database connection strings in feeds.yaml

# Run the application
python main.py
```

The backend will start on `http://localhost:8000`

### 2. Frontend Setup (React)

If you want to use the React dashboard in a separate environment:

```bash
# Create React app
npx create-react-app feed-monitor-frontend
cd feed-monitor-frontend

# Install additional dependencies
npm install lucide-react axios recharts

# Replace src/App.js with the provided React component
# Update API endpoints to point to your backend

# Start development server
npm start
```

### 3. Database Configuration

#### PostgreSQL Setup (Recommended for Production)
```sql
-- Create database
CREATE DATABASE feed_monitor;

-- Create user
CREATE USER feed_monitor_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE feed_monitor TO feed_monitor_user;

-- Connect to database and create tables
\c feed_monitor;

-- Feed status tracking table
CREATE TABLE feed_status (
    id SERIAL PRIMARY KEY,
    feed_name VARCHAR(255) NOT NULL,
    cob_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    record_count INTEGER DEFAULT 0,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_time VARCHAR(10),
    UNIQUE(feed_name, cob_date)
);

-- Create indexes
CREATE INDEX idx_feed_status_feed_date ON feed_status(feed_name, cob_date);
CREATE INDEX idx_feed_status_date ON feed_status(cob_date);
```

#### SQLite Setup (Development)
The application will automatically create SQLite database with sample data for testing.

### 4. Configuration

Update `config/feeds.yaml` with your actual feed configurations:

```yaml
feeds:
  - name: "Your Feed Name"
    source_table: "your_table_name"
    date_column: "your_date_column"
    expected_time: "HH:MM"
    tolerance_minutes: 60
    weekend_expected: false
    min_records: 100
    connection_string: "postgresql://user:pass@host:port/database"
```

### 5. Environment Variables

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/feed_monitor

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Scheduling
CHECK_INTERVAL_MINUTES=10

# Alerting
SMTP_SERVER=smtp.company.com
SMTP_PORT=587
SMTP_USERNAME=alerts@company.com
SMTP_PASSWORD=your_smtp_password

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

## API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /api/feeds/status` - Get 90-day status summary for all feeds
- `GET /api/feeds/{feed_name}/status?cob_date=YYYY-MM-DD` - Get specific feed status
- `POST /api/feeds/check` - Manually trigger feed check
- `GET /api/config/feeds` - Get feed configurations

### Status Values
- `received` - Feed received successfully with expected record count
- `delayed` - Feed received but after expected time + tolerance
- `missing` - No data found for the COB date
- `partial` - Data found but below minimum record threshold
- `failed` - Error occurred during check
- `unknown` - Status not determined

## Production Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual containers
docker build -f docker/Dockerfile.backend -t feed-monitor-backend .
docker build -f docker/Dockerfile.frontend -t feed-monitor-frontend .

docker run -d -p 8000:8000 --name feed-monitor-backend feed-monitor-backend
docker run -d -p 3000:3000 --name feed-monitor-frontend feed-monitor-frontend
```

### Systemd Service (Linux)

Create `/etc/systemd/system/feed-monitor.service`:

```ini
[Unit]
Description=Feed Monitor Service
After=network.target

[Service]
Type=simple
User=feedmonitor
WorkingDirectory=/opt/feed-monitor
ExecStart=/opt/feed-monitor/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable feed-monitor
sudo systemctl start feed-monitor
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Maintenance

### Log Monitoring
- Application logs are written to stdout/stderr
- Configure log rotation and monitoring
- Set up alerts for ERROR level logs

### Database Maintenance
```sql
-- Clean old records (optional, based on retention policy)
DELETE FROM feed_status 
WHERE last_checked < NOW() - INTERVAL '365 days';

-- Analyze table performance
ANALYZE feed_status;
```

### Health Checks
The API provides health check endpoints that can be used with monitoring tools like Nagios, Prometheus, or AWS CloudWatch.

## Customization

### Adding New Feed Types
1. Update `feeds.yaml` with new feed configuration
2. Ensure source database connectivity
3. Restart the application to reload configuration

### Custom Status Logic
Modify the `determine_status()` method in `FeedMonitor` class to implement custom business rules for status determination.

### Alert Integration
Implement custom alerting in the `services/alerting.py` module for integration with your organization's alerting systems.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify connection strings in feeds.yaml
   - Check database credentials and network connectivity
   - Ensure database exists and user has proper permissions

2. **Scheduler Not Running**
   - Check application logs for scheduler errors
   - Verify APScheduler configuration
   - Ensure application has proper permissions

3. **Missing Data**
   - Verify source table names and date columns
   - Check date format compatibility
   - Ensure timezone configurations are correct

4. **Performance Issues**
   - Add database indexes on date columns
   - Consider partitioning large historical tables
   - Implement connection pooling for high-volume feeds

### Debug Mode
Set `DEBUG=True` in environment variables for detailed logging and error messages.

## Support and Extension

This framework is designed to be highly extensible. Key extension points include:

- **Custom Data Sources**: Add support for APIs, file systems, or other data sources
- **Advanced Alerting**: Integration with PagerDuty, ServiceNow, or custom webhook systems
- **Data Quality Checks**: Extend beyond record counts to include data quality metrics
- **Reporting**: Add scheduled reports and trend analysis
- **Authentication**: Add user authentication and role-based access control

For additional features or support, refer to the API documentation at `http://localhost:8000/docs` when the application is running.