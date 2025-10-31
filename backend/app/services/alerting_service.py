"""Simple alerting service for monitoring critical system conditions"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.config import settings
from app.core.logging import logger
from app.services.metrics_service import metrics_service, MetricType


class AlertLevel(str):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertingService:
    """Service for monitoring metrics and sending alerts"""
    
    def __init__(self):
        """Initialize alerting service"""
        self.error_rate_threshold = 1.0  # 1% error rate threshold
        self.processing_time_threshold = 10000  # 10 seconds in milliseconds
        self.alert_cooldown = 300  # 5 minutes cooldown between similar alerts
        
        # Track last alert times to prevent spam
        self.last_alert_times = defaultdict(lambda: datetime.min)
        
        # Email configuration
        self.email_enabled = hasattr(settings, 'SMTP_HOST') and settings.SMTP_HOST
        self.smtp_host = getattr(settings, 'SMTP_HOST', None)
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.alert_email_to = getattr(settings, 'ALERT_EMAIL_TO', None)
        self.alert_email_from = getattr(settings, 'ALERT_EMAIL_FROM', self.smtp_username)
        
        logger.info(f"Alerting service initialized (email enabled: {self.email_enabled})")
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """
        Check if enough time has passed since last alert
        
        Args:
            alert_key: Unique key for the alert type
            
        Returns:
            True if alert should be sent
        """
        last_alert_time = self.last_alert_times[alert_key]
        time_since_last = (datetime.utcnow() - last_alert_time).total_seconds()
        
        return time_since_last >= self.alert_cooldown
    
    def _update_alert_time(self, alert_key: str):
        """Update the last alert time for a given alert key"""
        self.last_alert_times[alert_key] = datetime.utcnow()
    
    def _send_email_alert(self, subject: str, body: str, level: str = AlertLevel.WARNING):
        """
        Send email alert
        
        Args:
            subject: Email subject
            body: Email body
            level: Alert level
        """
        if not self.email_enabled:
            logger.warning(f"Email alerting not configured. Alert: {subject}")
            return
        
        if not self.alert_email_to:
            logger.warning("No alert email recipient configured")
            return
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.alert_email_from
            msg['To'] = self.alert_email_to
            msg['Subject'] = f"[{level}] {subject}"
            
            # Add timestamp and level to body
            full_body = f"""
Alert Level: {level}
Timestamp: {datetime.utcnow().isoformat()}

{body}

---
Face Authentication System
"""
            
            msg.attach(MIMEText(full_body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
    
    def _log_alert(self, subject: str, body: str, level: str):
        """Log alert to console"""
        log_message = f"[{level}] {subject}: {body}"
        
        if level == AlertLevel.CRITICAL:
            logger.critical(log_message)
        elif level == AlertLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def send_alert(self, subject: str, body: str, level: str = AlertLevel.WARNING, alert_key: Optional[str] = None):
        """
        Send an alert
        
        Args:
            subject: Alert subject
            body: Alert body/description
            level: Alert level (INFO, WARNING, CRITICAL)
            alert_key: Optional unique key for cooldown tracking
        """
        # Use subject as alert key if not provided
        if alert_key is None:
            alert_key = subject
        
        # Check cooldown
        if not self._should_send_alert(alert_key):
            logger.debug(f"Alert suppressed due to cooldown: {subject}")
            return
        
        # Log alert
        self._log_alert(subject, body, level)
        
        # Send email for WARNING and CRITICAL alerts
        if level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
            self._send_email_alert(subject, body, level)
        
        # Update alert time
        self._update_alert_time(alert_key)
    
    def check_error_rate(self):
        """Check if error rate exceeds threshold"""
        error_rate = metrics_service.get_error_rate(window_seconds=60)
        
        if error_rate > self.error_rate_threshold:
            subject = f"High Error Rate Detected: {error_rate:.2f}%"
            body = f"""
The system error rate has exceeded the threshold of {self.error_rate_threshold}%.

Current Error Rate: {error_rate:.2f}%
Time Window: Last 60 seconds

Recent Errors:
"""
            # Add recent errors to body
            recent_errors = metrics_service.get_recent_errors(limit=5)
            for error in recent_errors:
                body += f"\n- [{error['timestamp']}] {error['metric_type']}: {error['error_message']}"
            
            body += "\n\nPlease investigate the cause of these errors."
            
            self.send_alert(
                subject=subject,
                body=body,
                level=AlertLevel.WARNING,
                alert_key="high_error_rate"
            )
    
    def check_processing_time(self, metric_type: MetricType):
        """
        Check if processing time exceeds threshold
        
        Args:
            metric_type: Type of metric to check
        """
        stats = metrics_service.get_latency_stats(metric_type)
        
        if stats['count'] > 0 and stats['p95_ms'] > self.processing_time_threshold:
            subject = f"Slow Processing Detected: {metric_type}"
            body = f"""
The {metric_type} processing time has exceeded the threshold.

P95 Latency: {stats['p95_ms']:.2f}ms
Threshold: {self.processing_time_threshold}ms
Average Latency: {stats['avg_ms']:.2f}ms
Max Latency: {stats['max_ms']:.2f}ms

Sample Count: {stats['count']}

This may indicate performance degradation or resource constraints.
"""
            
            self.send_alert(
                subject=subject,
                body=body,
                level=AlertLevel.WARNING,
                alert_key=f"slow_processing_{metric_type}"
            )
    
    def check_all_metrics(self):
        """Check all metrics and send alerts if thresholds are exceeded"""
        # Check error rate
        self.check_error_rate()
        
        # Check processing times for key metrics
        for metric_type in [MetricType.FACE_RECOGNITION, MetricType.DUPLICATE_DETECTION, MetricType.FAISS_SEARCH]:
            self.check_processing_time(metric_type)
    
    def send_critical_error_alert(self, error_message: str, context: Optional[dict] = None):
        """
        Send critical error alert
        
        Args:
            error_message: Error message
            context: Optional context information
        """
        subject = "Critical System Error"
        body = f"""
A critical error has occurred in the Face Authentication System.

Error: {error_message}

"""
        
        if context:
            body += "Context:\n"
            for key, value in context.items():
                body += f"  {key}: {value}\n"
        
        body += "\nImmediate attention required."
        
        self.send_alert(
            subject=subject,
            body=body,
            level=AlertLevel.CRITICAL,
            alert_key=f"critical_error_{error_message[:50]}"
        )
    
    def send_info_alert(self, subject: str, body: str):
        """
        Send informational alert
        
        Args:
            subject: Alert subject
            body: Alert body
        """
        self.send_alert(subject, body, level=AlertLevel.INFO)


# Global alerting service instance
alerting_service = AlertingService()
