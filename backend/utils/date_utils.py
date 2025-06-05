from datetime import datetime, date, timedelta, time
from typing import List, Optional, Union
import pytz
from dateutil.parser import parse
import logging

logger = logging.getLogger(__name__)

class DateUtils:
    @staticmethod
    def get_business_days(start_date: Union[str, date], end_date: Union[str, date]) -> List[date]:
        """Get list of business days between two dates"""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        business_days = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
                business_days.append(current_date)
            current_date += timedelta(days=1)
        
        return business_days
    
    @staticmethod
    def is_business_day(target_date: Union[str, date]) -> bool:
        """Check if a date is a business day"""
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        return target_date.weekday() < 5
    
    @staticmethod
    def is_holiday(target_date: Union[str, date], holidays: List[str]) -> bool:
        """Check if a date is a holiday"""
        if isinstance(target_date, date):
            target_date = target_date.isoformat()
        
        return target_date in holidays
    
    @staticmethod
    def get_previous_business_day(target_date: Union[str, date]) -> date:
        """Get the previous business day"""
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        previous_day = target_date - timedelta(days=1)
        
        while previous_day.weekday() >= 5:  # Skip weekends
            previous_day -= timedelta(days=1)
        
        return previous_day
    
    @staticmethod
    def get_cob_date(timezone_str: str = 'UTC') -> date:
        """Get current COB (Close of Business) date"""
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        
        # If it's before 6 AM, consider it as previous day's COB
        if now.hour < 6:
            return (now - timedelta(days=1)).date()
        else:
            return now.date()
    
    @staticmethod
    def parse_time_string(time_str: str) -> time:
        """Parse time string to time object"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except ValueError:
            logger.error(f"Invalid time format: {time_str}")
            raise
    
    @staticmethod
    def is_within_tolerance(expected_time: str, actual_time: datetime, tolerance_minutes: int) -> bool:
        """Check if actual time is within tolerance of expected time"""
        try:
            expected = DateUtils.parse_time_string(expected_time)
            actual_time_only = actual_time.time()
            
            # Calculate tolerance window
            expected_dt = datetime.combine(actual_time.date(), expected)
            tolerance_delta = timedelta(minutes=tolerance_minutes)
            
            start_window = expected_dt - tolerance_delta
            end_window = expected_dt + tolerance_delta
            
            return start_window <= actual_time <= end_window
        except Exception as e:
            logger.error(f"Error checking time tolerance: {e}")
            return False
    
    @staticmethod
    def format_duration(minutes: int) -> str:
        """Format duration in minutes to human readable format"""
        if minutes < 60:
            return f"{minutes}m"
        elif minutes < 1440:  # Less than 24 hours
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
        else:
            days = minutes // 1440
            remaining_minutes = minutes % 1440
            hours = remaining_minutes // 60
            mins = remaining_minutes % 60
            
            result = f"{days}d"
            if hours > 0:
                result += f" {hours}h"
            if mins > 0:
                result += f" {mins}m"
            
            return result
    
    @staticmethod
    def get_date_range(days: int) -> tuple:
        """Get date range for the last N days"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date