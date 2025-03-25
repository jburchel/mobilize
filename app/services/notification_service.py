"""
Notification Service Module

This module provides notification functionality for the application.
During development, notifications are logged rather than sent.
"""

import logging
from flask import current_app
from app.models.user import User

logger = logging.getLogger(__name__)

def send_notification(user_id=None, user=None, notification_type='info', notification_data=None, title=None, message=None, link=None, link_text=None):
    """
    Send a notification to a user or log it during development.
    
    Args:
        user_id (int, optional): ID of the user to send notification to (alternative to user object)
        user (User, optional): User object to send notification to
        notification_type (str): Type of notification (info, warning, error, success, task_reminder, etc.)
        notification_data (dict, optional): Dictionary containing notification data
        title (str, optional): Notification title
        message (str, optional): Notification message
        link (str, optional): Link to include in notification
        link_text (str, optional): Text for the link
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get user object if only ID provided
        if user_id and not user:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User with ID {user_id} not found")
                return False

        # Extract data from notification_data if provided
        if notification_data:
            title = notification_data.get('title', title)
            message = notification_data.get('message', message)
            link = notification_data.get('link', link)
            link_text = notification_data.get('link_text', link_text)
        
        # Ensure we have required data
        if not user or not title or not message:
            logger.error("Missing required data for notification")
            return False
            
        # Log the notification
        logger.info(f"NOTIFICATION WOULD BE SENT - To: {user.email}, Title: {title}, Type: {notification_type}")
        logger.info(f"Message: {message}")
        if link:
            logger.info(f"Link: {link} ({link_text or 'Click here'})")
            
        # In the future, this would interact with the notification system
        # For now, we just log it
        return True
    
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return False 