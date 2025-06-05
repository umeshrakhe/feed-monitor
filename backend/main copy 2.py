# main.py - FastAPI Backend for Feed Monitoring Framework
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import sqlite3
import yaml
import json
import logging
from dataclasses import dataclass
from enum import Enum
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Feed Monitoring Framework", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class FeedStatus(str, Enum):
    RECEIVED = "received"
    DELAYED = "delayed"
    MISSING = "missing"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"

class FeedStatusResponse(BaseModel):
    feed_name: str
    cob_date: str
    status: FeedStatus
    record_count: int
    last_updated: datetime
    expected_time: Optional[str] = None

class FeedSummaryResponse(BaseModel):
    feed_name: str
    daily_status: Dict[str, Dict]  # date -> {status, count, day_of_week}

@dataclass
class FeedConfig:
    name: str
    source_table: str
    date_column: str
    expected_time: str
    tolerance_minutes: int
    weekend_expected: bool
    min_records: int
    connection_string: str

class FeedMonitor:
    def __init__(self, config_path: str = "config/feeds.yaml"):
        self.config_path = config_path
        self.feeds_config = self.load_config()
        self.init_database()
        
    def load_config(self) -> List[FeedConfig]:
        """Load feed configurations from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                config_data = yaml.safe_load(file)
                feeds = []
                for feed_data in config_data.get('feeds', []):
                    feeds.append(FeedConfig(**feed_data))
                return feeds
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found. Using default config.")
            return self.get_default_config()
    
    def get_default_config(self) -> List[FeedConfig]:
        """Return default configuration for demo purposes"""
        return [
            FeedConfig(
                name="Customer Transactions",
                source_table="customer_transactions",
                date_column="transaction_date",
                expected_time="09:00",
                tolerance_minutes=60,
                weekend_expected=False,
                min_records=1000,
                connection_string="sqlite:///demo.db"
            ),
            FeedConfig(
                name="Product Catalog",
                source_table="product_catalog",
                date_column="update_date",
                expected_time="06:00",
                tolerance_minutes=30,
                weekend_expected=True,
                min_records=100,
                connection_string="sqlite:///demo.db"
            ),
            FeedConfig(
                name="Order Processing",
                source_table="orders",
                date_column="order_date",
                expected_time="10:30",
                tolerance_minutes=45,
                weekend_expected=False,
                min_records=500,
                connection_string="sqlite:///demo.db"
            )
        ]
    
    def init_database(self):
        """Initialize SQLite database for demo and monitoring metadata"""
        conn = sqlite3.connect('demo.db')
        cursor = conn.cursor()
        
        # Create demo tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_transactions (
                id INTEGER PRIMARY KEY,
                transaction_date DATE,
                customer_id INTEGER,
                amount DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_catalog (
                id INTEGER PRIMARY KEY,
                update_date DATE,
                product_name TEXT,
                price DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                order_date DATE,
                customer_id INTEGER,
                total DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create feed status tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feed_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_name TEXT,
                cob_date DATE,
                status TEXT,
                record_count INTEGER,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expected_time TEXT,
                UNIQUE(feed_name, cob_date)
            )
        ''')
        
        # Insert sample data for demo
        self.insert_sample_data(cursor)
        
        conn.commit()
        conn.close()
    
    def insert_sample_data(self, cursor):
        """Insert sample data for demonstration"""
        import random
        from datetime import datetime, timedelta
        
        # Generate data for last 10 days
        end_date = datetime.now().date()
        
        for i in range(10):
            current_date = end_date - timedelta(days=i)
            
            # Customer transactions (skip weekends sometimes)
            if current_date.weekday() < 5 or random.random() > 0.3:
                count = random.randint(800, 1500)
                for j in range(count):
                    cursor.execute('''
                        INSERT OR IGNORE INTO customer_transactions 
                        (transaction_date, customer_id, amount) 
                        VALUES (?, ?, ?)
                    ''', (current_date, random.randint(1, 1000), random.uniform(10, 500)))
            
            # Product catalog (daily updates)
            count = random.randint(80, 150)
            for j in range(count):
                cursor.execute('''
                    INSERT OR IGNORE INTO product_catalog 
                    (update_date, product_name, price) 
                    VALUES (?, ?, ?)
                ''', (current_date, f"Product_{j}", random.uniform(5, 200)))
            
            # Orders (skip weekends)
            if current_date.weekday() < 5:
                count = random.randint(400, 800)
                for j in range(count):
                    cursor.execute('''
                        INSERT OR IGNORE INTO orders 
                        (order_date, customer_id, total) 
                        VALUES (?, ?, ?)
                    ''', (current_date, random.randint(1, 1000), random.uniform(20, 300)))
    
    def check_feed_status(self, feed_config: FeedConfig, cob_date: date) -> FeedStatusResponse:
        """Check status of a specific feed for given COB date"""
        try:
            conn = sqlite3.connect('demo.db')
            cursor = conn.cursor()
            
            # Count records for the COB date
            query = f"SELECT COUNT(*) FROM {feed_config.source_table} WHERE {feed_config.date_column} = ?"
            cursor.execute(query, (cob_date,))
            record_count = cursor.fetchone()[0]
            
            # Determine status
            status = self.determine_status(feed_config, cob_date, record_count)
            
            # Update feed status table
            cursor.execute('''
                INSERT OR REPLACE INTO feed_status 
                (feed_name, cob_date, status, record_count, last_checked, expected_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (feed_config.name, cob_date, status.value, record_count, 
                  datetime.now(), feed_config.expected_time))
            
            conn.commit()
            conn.close()
            
            return FeedStatusResponse(
                feed_name=feed_config.name,
                cob_date=cob_date.isoformat(),
                status=status,
                record_count=record_count,
                last_updated=datetime.now(),
                expected_time=feed_config.expected_time
            )
            
        except Exception as e:
            logger.error(f"Error checking feed {feed_config.name}: {str(e)}")
            return FeedStatusResponse(
                feed_name=feed_config.name,
                cob_date=cob_date.isoformat(),
                status=FeedStatus.FAILED,
                record_count=0,
                last_updated=datetime.now(),
                expected_time=feed_config.expected_time
            )
    
    def determine_status(self, feed_config: FeedConfig, cob_date: date, record_count: int) -> FeedStatus:
        """Determine feed status based on configuration and data"""
        # Check if it's weekend and feed is not expected
        if cob_date.weekday() >= 5 and not feed_config.weekend_expected:
            return FeedStatus.RECEIVED if record_count == 0 else FeedStatus.RECEIVED
        
        # Check minimum records threshold
        if record_count == 0:
            return FeedStatus.MISSING
        elif record_count < feed_config.min_records:
            return FeedStatus.PARTIAL
        else:
            return FeedStatus.RECEIVED
    
    def check_all_feeds(self):
        """Check all configured feeds for previous COB date"""
        yesterday = datetime.now().date() - timedelta(days=1)
        logger.info(f"Checking all feeds for COB date: {yesterday}")
        
        for feed_config in self.feeds_config:
            try:
                result = self.check_feed_status(feed_config, yesterday)
                logger.info(f"Feed {feed_config.name}: {result.status} ({result.record_count} records)")
            except Exception as e:
                logger.error(f"Failed to check feed {feed_config.name}: {str(e)}")

# Initialize monitor
monitor = FeedMonitor()

# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=monitor.check_all_feeds,
    trigger=IntervalTrigger(minutes=10),
    id='feed_check_job',
    name='Check all feeds every 10 minutes',
    replace_existing=True
)
scheduler.start()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    logger.info("Feed Monitor API started")
    # Run initial check
    monitor.check_all_feeds()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/")
async def root():
    return {"message": "Feed Monitoring Framework API", "version": "1.0.0"}

@app.get("/api/feeds/status", response_model=List[FeedSummaryResponse])
async def get_feeds_status():
    """Get 90 days status summary for all feeds"""
    try:
        conn = sqlite3.connect('demo.db')
        cursor = conn.cursor()
        
        # Get last 90 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        
        feeds_summary = []
        
        for feed_config in monitor.feeds_config:
            daily_status = {}
            
            # Generate all dates in range
            current_date = start_date
            while current_date <= end_date:
                day_name = current_date.strftime('%A')[:3]  # Mon, Tue, etc.
                
                # Check if we have status data
                cursor.execute('''
                    SELECT status, record_count FROM feed_status 
                    WHERE feed_name = ? AND cob_date = ?
                ''', (feed_config.name, current_date))
                
                result = cursor.fetchone()
                if result:
                    status, count = result
                else:
                    # If no data, check actual table for historical data
                    query = f"SELECT COUNT(*) FROM {feed_config.source_table} WHERE {feed_config.date_column} = ?"
                    cursor.execute(query, (current_date,))
                    count = cursor.fetchone()[0]
                    status = monitor.determine_status(feed_config, current_date, count).value
                
                daily_status[current_date.isoformat()] = {
                    "status": status,
                    "count": count,
                    "day_of_week": day_name,
                    "is_weekend": current_date.weekday() >= 5
                }
                
                current_date += timedelta(days=1)
            
            feeds_summary.append(FeedSummaryResponse(
                feed_name=feed_config.name,
                daily_status=daily_status
            ))
        
        conn.close()
        return feeds_summary
        
    except Exception as e:
        logger.error(f"Error getting feeds status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/feeds/{feed_name}/status")
async def get_feed_status(feed_name: str, cob_date: Optional[str] = None):
    """Get specific feed status for a date"""
    try:
        target_date = datetime.strptime(cob_date, '%Y-%m-%d').date() if cob_date else datetime.now().date() - timedelta(days=1)
        
        feed_config = next((f for f in monitor.feeds_config if f.name == feed_name), None)
        if not feed_config:
            raise HTTPException(status_code=404, detail="Feed not found")
        
        result = monitor.check_feed_status(feed_config, target_date)
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error getting feed status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feeds/check")
async def trigger_feed_check():
    """Manually trigger feed check"""
    try:
        monitor.check_all_feeds()
        return {"message": "Feed check triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering feed check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/feeds")
async def get_feeds_config():
    """Get current feed configurations"""
    return [
        {
            "name": feed.name,
            "source_table": feed.source_table,
            "expected_time": feed.expected_time,
            "weekend_expected": feed.weekend_expected,
            "min_records": feed.min_records
        }
        for feed in monitor.feeds_config
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)