"""
Email utilities for sending emails from the application.
"""
import logging
from typing import List, Optional
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)

def send_email(recipients, subject, html_content=None, text_content=None, sender=None, cc=None, bcc=None, attachments=None):
    """
    Send an email using Flask-Mail
    
    Args:
        recipients (list): List of email addresses
        subject (str): Email subject
        html_content (str, optional): HTML content of the email
        text_content (str, optional): Plain text content of the email
        sender (str, optional): Sender email address (defaults to MAIL_DEFAULT_SENDER)
        cc (list, optional): List of CC recipients
        bcc (list, optional): List of BCC recipients
        attachments (list, optional): List of (filename, data) tuples
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not recipients:
        logger.error("No recipients provided for email")
        return False
    
    if not html_content and not text_content:
        logger.error("No content provided for email")
        return False
    
    try:
        # Create message
        msg = Message(
            subject=subject,
            recipients=recipients,
            sender=sender or current_app.config.get('MAIL_DEFAULT_SENDER'),
            cc=cc,
            bcc=bcc
        )
        
        # Set content
        if html_content:
            msg.html = html_content
        if text_content:
            msg.body = text_content
            
        # Add attachments
        if attachments:
            for filename, data in attachments:
                msg.attach(filename, data)
                
        # Send email
        mail.send(msg)
        logger.info(f"Email sent to {', '.join(recipients)}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False 