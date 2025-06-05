# backend/models/feed_config.py
from dataclasses import dataclass
from typing import Optional, List
from datetime import time

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
    
    def get_expected_time(self) -> time:
        """Convert expected_time string to time object"""
        hour, minute = map(int, self.expected_time.split(':'))
        return time(hour, minute)

@dataclass
class GlobalSettings:
    check_interval_minutes: int = 10
    retention_days: int = 365
    alert_channels: dict = None
    holidays: List[str] = None
    business_hours: dict = None
    
    def __post_init__(self):
        if self.alert_channels is None:
            self.alert_channels = {}
        if self.holidays is None:
            self.holidays = []
        if self.business_hours is None:
            self.business_hours = {"start": "06:00", "end": "20:00", "timezone": "UTC"}
