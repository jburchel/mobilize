"""
Email Service Module

This module provides email functionality for the application.
During development, emails are logged rather than sent.
"""

import logging
from flask import current_app
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def send_email(recipients, subject, html_body, sender=None, attachments=None):
    """
    Send an email or log it during development.
    
    Args:
        recipients (list): List of email addresses to send to
        subject (str): Email subject
        html_body (str): HTML content of the email
        sender (str, optional): Email sender address
        attachments (list, optional): List of attachment file paths
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the default sender if not provided
        if not sender and current_app.config.get('MAIL_DEFAULT_SENDER'):
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        elif not sender:
            sender = "noreply@example.com"
            
        # Format recipients as a comma-separated string if it's a list
        if isinstance(recipients, list):
            recipients_str = ", ".join(recipients)
        else:
            recipients_str = recipients
            
        # Log the email instead of sending it
        logger.info(f"EMAIL WOULD BE SENT - From: {sender}, To: {recipients_str}, Subject: {subject}")
        
        # Create a log file in the logs directory if it exists
        logs_dir = os.path.join(current_app.root_path, '..', 'logs')
        if os.path.exists(logs_dir):
            log_file = os.path.join(logs_dir, 'email_logs.txt')
            with open(log_file, 'a') as f:
                f.write(f"\n--- {datetime.now()} ---\n")
                f.write(f"From: {sender}\n")
                f.write(f"To: {recipients_str}\n")
                f.write(f"Subject: {subject}\n")
                f.write(f"Body:\n{html_body}\n")
                f.write(f"--- END EMAIL ---\n")
        
        # In the future, this is where we would integrate with Gmail API
        return True
    
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def send_pipeline_reminder_email(user, stage, pipeline, contacts, days):
    """
    Send an email reminder about contacts in a pipeline stage.
    
    Args:
        user (User): User to send the reminder to
        stage (PipelineStage): Pipeline stage
        pipeline (Pipeline): Pipeline
        contacts (list): List of contacts in the stage
        days (int): Number of days the contacts have been in the stage
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from flask import render_template
        
        subject = f"Pipeline Reminder: {len(contacts)} contacts in {stage.name} for {days} days"
        
        # Render the template
        html_body = render_template(
            'email/pipeline_reminder.html',
            user=user,
            stage=stage,
            pipeline=pipeline,
            contacts=contacts,
            days=days
        )
        
        # Send the email
        return send_email(
            recipients=[user.email],
            subject=subject,
            html_body=html_body
        )
    
    except Exception as e:
        logger.error(f"Failed to send reminder email: {str(e)}")
        return False 