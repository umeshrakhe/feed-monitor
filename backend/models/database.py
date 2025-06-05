from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class FeedStatus(Base):
    __tablename__ = "feed_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    feed_name = Column(String(255), nullable=False)
    cob_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)
    record_count = Column(Integer, default=0)
    last_checked = Column(DateTime, default=func.now())
    expected_time = Column(String(10))
    error_message = Column(Text)
    
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()