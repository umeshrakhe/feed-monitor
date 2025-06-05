# backend/models/database.py - Database connection and models
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from typing import Optional

Base = declarative_base()

class FeedStatus(Base):
    """Model for tracking feed status"""
    __tablename__ = "feed_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    feed_name = Column(String(255), nullable=False)
    cob_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)
    record_count = Column(Integer, default=0)
    last_checked = Column(DateTime, default=datetime.utcnow)
    expected_time = Column(String(10))
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<FeedStatus(feed_name='{self.feed_name}', cob_date='{self.cob_date}', status='{self.status}')>"

class FeedConfiguration(Base):
    """Model for storing feed configurations"""
    __tablename__ = "feed_configurations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    source_table = Column(String(255), nullable=False)
    date_column = Column(String(100), nullable=False)
    expected_time = Column(String(10), nullable=False)
    tolerance_minutes = Column(Integer, default=60)
    weekend_expected = Column(Boolean, default=False)
    min_records = Column(Integer, default=1)
    connection_string = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FeedConfiguration(name='{self.name}', source_table='{self.source_table}')>"

class AlertLog(Base):
    """Model for tracking sent alerts"""
    __tablename__ = "alert_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    feed_name = Column(String(255), nullable=False)
    cob_date = Column(Date, nullable=False)
    alert_type = Column(String(50), nullable=False)  # email, slack, etc.
    alert_status = Column(String(20), nullable=False)  # sent, failed
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<AlertLog(feed_name='{self.feed_name}', alert_type='{self.alert_type}', status='{self.alert_status}')>"

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///feed_monitor.db")
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(
                self.database_url,
                echo=os.getenv("DEBUG", "False").lower() == "true"
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
        except Exception as e:
            raise Exception(f"Failed to initialize database: {str(e)}")
    
    def get_session(self):
        """Get database session"""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()

# Global database manager instance
db_manager = DatabaseManager()

def get_db():
    """Dependency to get database session"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()