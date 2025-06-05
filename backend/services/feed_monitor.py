import logging
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from models.feed_config import FeedConfig
from models.database import DatabaseManager, FeedStatus as FeedStatusModel
from enum import Enum

logger = logging.getLogger(__name__)

class FeedStatus(str, Enum):
    RECEIVED = "received"
    DELAYED = "delayed"
    MISSING = "missing"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"

class FeedMonitorService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def check_feed_status(self, feed_config: FeedConfig, cob_date: date) -> dict:
        """Check status of a specific feed for given COB date"""
        try:
            # Create connection to source database
            engine = create_engine(feed_config.connection_string)
            
            with engine.connect() as conn:
                # Count records for the COB date
                query = text(f"SELECT COUNT(*) FROM {feed_config.source_table} WHERE {feed_config.date_column} = :cob_date")
                result = conn.execute(query, {"cob_date": cob_date})
                record_count = result.scalar()
            
            # Determine status
            status = self._determine_status(feed_config, cob_date, record_count)
            
            # Update feed status in monitoring database
            self._update_feed_status(feed_config, cob_date, status, record_count)
            
            return {
                "feed_name": feed_config.name,
                "cob_date": cob_date.isoformat(),
                "status": status.value,
                "record_count": record_count,
                "last_updated": datetime.now(),
                "expected_time": feed_config.expected_time
            }
            
        except Exception as e:
            logger.error(f"Error checking feed {feed_config.name}: {str(e)}")
            self._update_feed_status(feed_config, cob_date, FeedStatus.FAILED, 0, str(e))
            
            return {
                "feed_name": feed_config.name,
                "cob_date": cob_date.isoformat(),
                "status": FeedStatus.FAILED.value,
                "record_count": 0,
                "last_updated": datetime.now(),
                "expected_time": feed_config.expected_time,
                "error": str(e)
            }
    
    def _determine_status(self, feed_config: FeedConfig, cob_date: date, record_count: int) -> FeedStatus:
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
            # Check if delayed (would need time comparison logic)
            return FeedStatus.RECEIVED
    
    def _update_feed_status(self, feed_config: FeedConfig, cob_date: date, status: FeedStatus, 
                           record_count: int, error_message: Optional[str] = None):
        """Update feed status in monitoring database"""
        try:
            with self.db_manager.get_session() as session:
                # Check if record exists
                existing = session.query(FeedStatusModel).filter(
                    FeedStatusModel.feed_name == feed_config.name,
                    FeedStatusModel.cob_date == cob_date
                ).first()
                
                if existing:
                    existing.status = status.value
                    existing.record_count = record_count
                    existing.last_checked = datetime.now()
                    existing.error_message = error_message
                else:
                    new_status = FeedStatusModel(
                        feed_name=feed_config.name,
                        cob_date=cob_date,
                        status=status.value,
                        record_count=record_count,
                        last_checked=datetime.now(),
                        expected_time=feed_config.expected_time,
                        error_message=error_message
                    )
                    session.add(new_status)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error updating feed status: {e}")
    
    def get_feed_summary(self, days: int = 90) -> List[dict]:
        """Get feed status summary for specified number of days"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            with self.db_manager.get_session() as session:
                results = session.query(FeedStatusModel).filter(
                    FeedStatusModel.cob_date >= start_date,
                    FeedStatusModel.cob_date <= end_date
                ).all()
                
                # Group by feed name
                feed_data = {}
                for result in results:
                    if result.feed_name not in feed_data:
                        feed_data[result.feed_name] = {}
                    
                    feed_data[result.feed_name][result.cob_date.isoformat()] = {
                        "status": result.status,
                        "count": result.record_count,
                        "day_of_week": result.cob_date.strftime('%a'),
                        "is_weekend": result.cob_date.weekday() >= 5
                    }
                
                return [
                    {
                        "feed_name": feed_name,
                        "daily_status": daily_status
                    }
                    for feed_name, daily_status in feed_data.items()
                ]
                
        except Exception as e:
            logger.error(f"Error getting feed summary: {e}")
            return []