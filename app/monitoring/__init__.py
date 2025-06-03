"""
Monitoring and alerting system for the application.
"""

import logging
import time
import os
import threading
import requests
from datetime import datetime
from flask import Flask, request, current_app

class ApplicationMonitor:
    """Monitor application health and performance."""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger('app.monitor')
        self.alert_endpoints = []
        self.last_error_time = None
        self.error_count = 0
        self.is_monitoring = False
        self.monitor_thread = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the monitor with a Flask app."""
        self.app = app
        
        # Register middleware for request monitoring
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
        
        # Register error handlers
        app.register_error_handler(500, self.handle_server_error)
        
        # Configure alert endpoints from environment variables
        self.configure_alert_endpoints()
        
        # Start the health check monitor
        self.start_health_monitor()
        
        app.logger.info("Application monitoring initialized")
    
    def configure_alert_endpoints(self):
        """Configure alert endpoints from environment variables."""
        # Slack webhook
        slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
        if slack_webhook:
            self.alert_endpoints.append({
                'type': 'slack',
                'url': slack_webhook
            })
        
        # Email alerts
        alert_email = os.environ.get('ALERT_EMAIL')
        if alert_email:
            self.alert_endpoints.append({
                'type': 'email',
                'address': alert_email
            })
        
        # Custom webhook
        custom_webhook = os.environ.get('CUSTOM_ALERT_WEBHOOK')
        if custom_webhook:
            self.alert_endpoints.append({
                'type': 'webhook',
                'url': custom_webhook
            })
    
    def before_request(self):
        """Record the start time of the request."""
        request.start_time = time.time()
    
    def after_request(self, response):
        """Monitor response times and status codes."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests (more than 500ms)
            if duration > 0.5:
                self.logger.warning(
                    f"SLOW REQUEST: {request.method} {request.path} took {duration:.2f}s"
                )
            
            # Add Server-Timing header for performance debugging
            response.headers['Server-Timing'] = f'total;dur={duration * 1000:.0f}'
            
            # Monitor for error responses
            if response.status_code >= 500:
                self.record_error(f"HTTP {response.status_code}: {request.path}")
        
        return response
    
    def teardown_request(self, exception):
        """Handle exceptions during request processing."""
        if exception:
            self.record_error(f"Exception during request: {str(exception)}")
    
    def handle_server_error(self, error):
        """Handle 500 server errors."""
        self.record_error(f"Server error: {str(error)}")
        return "Internal Server Error", 500
    
    def record_error(self, error_message):
        """Record an error and send alerts if necessary."""
        now = datetime.now()
        self.last_error_time = now
        self.error_count += 1
        
        self.logger.error(f"Application error: {error_message}")
        
        # Send alert if this is the first error or if we've seen multiple errors
        if self.error_count == 1 or self.error_count % 5 == 0:
            self.send_alert(f"Application Error: {error_message}", {
                'error_count': self.error_count,
                'timestamp': now.isoformat(),
                'environment': os.environ.get('FLASK_ENV', 'unknown')
            })
    
    def send_alert(self, message, details=None):
        """Send an alert to all configured endpoints."""
        if not self.alert_endpoints:
            self.logger.warning("No alert endpoints configured. Alert not sent.")
            return
        
        for endpoint in self.alert_endpoints:
            try:
                if endpoint['type'] == 'slack':
                    self.send_slack_alert(endpoint['url'], message, details)
                elif endpoint['type'] == 'webhook':
                    self.send_webhook_alert(endpoint['url'], message, details)
                elif endpoint['type'] == 'email':
                    self.send_email_alert(endpoint['address'], message, details)
            except Exception as e:
                self.logger.error(f"Failed to send alert to {endpoint['type']}: {str(e)}")
    
    def send_slack_alert(self, webhook_url, message, details=None):
        """Send an alert to a Slack webhook."""
        payload = {
            "text": message,
            "attachments": [
                {
                    "color": "#ff0000",
                    "fields": [
                        {"title": key, "value": str(value), "short": True}
                        for key, value in (details or {}).items()
                    ]
                }
            ]
        }
        
        requests.post(webhook_url, json=payload)
    
    def send_webhook_alert(self, webhook_url, message, details=None):
        """Send an alert to a custom webhook."""
        payload = {
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        requests.post(webhook_url, json=payload)
    
    def send_email_alert(self, email_address, message, details=None):
        """Send an email alert."""
        if hasattr(current_app, 'mail'):
            from flask_mail import Message
            
            # Format details as HTML
            details_html = ""
            if details:
                details_html = "<ul>"
                for key, value in details.items():
                    details_html += f"<li><strong>{key}:</strong> {value}</li>"
                details_html += "</ul>"
            
            msg = Message(
                subject=f"[ALERT] {message}",
                recipients=[email_address],
                html=f"<h2>{message}</h2>{details_html}<p>Time: {datetime.now().isoformat()}</p>"
            )
            
            current_app.mail.send(msg)
    
    def start_health_monitor(self):
        """Start a background thread to monitor application health."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Health monitor started")
    
    def _health_monitor_loop(self):
        """Background thread that periodically checks application health."""
        while self.is_monitoring:
            try:
                # Sleep first to allow the application to fully initialize
                time.sleep(60)  # Check every minute
                
                # Perform health checks
                self._check_application_health()
            except Exception as e:
                self.logger.error(f"Error in health monitor: {str(e)}")
    
    def _check_application_health(self):
        """Perform application health checks."""
        # This would typically make an internal request to the health endpoint
        # For now, we'll just log that the check was performed
        self.logger.debug("Health check performed")
        
        # In a real implementation, you would check:
        # 1. Database connectivity
        # 2. External service dependencies
        # 3. Memory usage
        # 4. Response times
        # And send alerts if any issues are detected

# Create the monitor instance
monitor = ApplicationMonitor()

def init_app(app):
    """Initialize monitoring for the application."""
    monitor.init_app(app)
    return app