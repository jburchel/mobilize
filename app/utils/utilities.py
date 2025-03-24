"""General utility functions for the application."""

import re
import unicodedata
import uuid
from datetime import datetime

def slugify(value):
    """
    Convert a string to a URL-friendly slug.
    
    Args:
        value: The string to convert
        
    Returns:
        A URL-friendly version of the string
    """
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def generate_uuid():
    """Generate a random UUID string."""
    return str(uuid.uuid4())

def format_date(date, format_string='%Y-%m-%d'):
    """
    Format a date as a string.
    
    Args:
        date: The date to format
        format_string: The format string to use
        
    Returns:
        The formatted date string
    """
    if not date:
        return ''
    if isinstance(date, str):
        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return date
    return date.strftime(format_string)

def format_phone(phone_number):
    """
    Format a phone number for display.
    
    Args:
        phone_number: The phone number to format
        
    Returns:
        The formatted phone number
    """
    if not phone_number:
        return ''
    # Remove all non-numeric characters
    phone = re.sub(r'\D', '', phone_number)
    if len(phone) == 10:
        return f"({phone[0:3]}) {phone[3:6]}-{phone[6:]}"
    return phone_number 