from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from typing import List, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
    
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def shutdown(self):
        """Shutdown the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")
    
    def add_interval_job(self, job_id: str, func: Callable, minutes: int, description: str = ""):
        """Add an interval-based job"""
        try:
            self.scheduler.add_job(
                func=func,
                trigger=IntervalTrigger(minutes=minutes),
                id=job_id,
                name=description or f"Interval job {job_id}",
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                "type": "interval",
                "minutes": minutes,
                "description": description,
                "function": func.__name__
            }
            
            logger.info(f"Added interval job {job_id}: {description}")
            
        except Exception as e:
            logger.error(f"Error adding interval job {job_id}: {e}")
            raise
    
    def add_cron_job(self, job_id: str, func: Callable, cron_expression: str, description: str = ""):
        """Add a cron-based job"""
        try:
            # Parse cron expression (minute hour day month day_of_week)
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must have 5 parts")
            
            minute, hour, day, month, day_of_week = parts
            
            self.scheduler.add_job(
                func=func,
                trigger=CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                ),
                id=job_id,
                name=description or f"Cron job {job_id}",
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                "type": "cron",
                "cron_expression": cron_expression,
                "description": description,
                "function": func.__name__
            }
            
            logger.info(f"Added cron job {job_id}: {description}")
            
        except Exception as e:
            logger.error(f"Error adding cron job {job_id}: {e}")
            raise
    
    def remove_job(self, job_id: str):
        """Remove a job"""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Removed job {job_id}")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
    
    def get_jobs(self) -> List[dict]:
        """Get list of all jobs"""
        return [
            {
                "job_id": job_id,
                "next_run": self.scheduler.get_job(job_id).next_run_time.isoformat() if self.scheduler.get_job(job_id) else None,
                **job_info
            }
            for job_id, job_info in self.jobs.items()
        ]