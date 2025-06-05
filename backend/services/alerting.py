import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AlertingService:
    def __init__(self, config: Dict):
        self.config = config
        self.email_config = config.get('email', {})
        self.slack_config = config.get('slack', {})
    
    def send_alert(self, feed_name: str, status: str, cob_date: str, record_count: int, error_message: Optional[str] = None):
        """Send alert for feed status"""
        try:
            alert_data = {
                "feed_name": feed_name,
                "status": status,
                "cob_date": cob_date,
                "record_count": record_count,
                "timestamp": datetime.now().isoformat(),
                "error_message": error_message
            }
            
            # Send email alert
            if self.email_config.get('enabled', False):
                self._send_email_alert(alert_data)
            
            # Send Slack alert
            if self.slack_config.get('enabled', False):
                self._send_slack_alert(alert_data)
                
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def _send_email_alert(self, alert_data: Dict):
        """Send email alert"""
        try:
            subject = f"Feed Alert: {alert_data['feed_name']} - {alert_data['status'].upper()}"
            
            body = f"""
            Feed Monitor Alert
            
            Feed Name: {alert_data['feed_name']}
            Status: {alert_data['status'].upper()}
            COB Date: {alert_data['cob_date']}
            Record Count: {alert_data['record_count']}
            Timestamp: {alert_data['timestamp']}
            
            {'Error: ' + alert_data['error_message'] if alert_data['error_message'] else ''}
            
            Please investigate and take appropriate action.
            """
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('from_address', 'feed-monitor@company.com')
            msg['To'] = ', '.join(self.email_config.get('recipients', []))
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            
            if self.email_config.get('username') and self.email_config.get('password'):
                server.login(self.email_config['username'], self.email_config['password'])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {alert_data['feed_name']}")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def _send_slack_alert(self, alert_data: Dict):
        """Send Slack alert"""
        try:
            color = {
                'received': 'good',
                'delayed': 'warning',
                'missing': 'danger',
                'partial': 'warning',
                'failed': 'danger'
            }.get(alert_data['status'], 'danger')
            
            payload = {
                "channel": self.slack_config.get('channel', '#data-alerts'),
                "username": "Feed Monitor",
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"Feed Alert: {alert_data['feed_name']}",
                        "fields": [
                            {
                                "title": "Status",
                                "value": alert_data['status'].upper(),
                                "short": True
                            },
                            {
                                "title": "COB Date",
                                "value": alert_data['cob_date'],
                                "short": True
                            },
                            {
                                "title": "Record Count",
                                "value": str(alert_data['record_count']),
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert_data['timestamp'],
                                "short": True
                            }
                        ],
                        "footer": "Feed Monitoring Framework",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            if alert_data['error_message']:
                payload["attachments"][0]["fields"].append({
                    "title": "Error",
                    "value": alert_data['error_message'],
                    "short": False
                })
            
            response = requests.post(self.slack_config['webhook_url'], json=payload)
            response.raise_for_status()
            
            logger.info(f"Slack alert sent for {alert_data['feed_name']}")
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")