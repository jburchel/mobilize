import re
from email_validator import validate_email as validate_email_format, EmailNotValidError

def validate_email(email):
    """
    Validate an email address format.
    Returns (is_valid, error_message)
    """
    if not email:
        return False, "Email address is required"
    
    try:
        # Validate the email format
        validate_email_format(email)
        return True, ""
    except EmailNotValidError as e:
        return False, str(e)

def validate_phone(phone):
    """
    Validate a phone number format.
    Returns (is_valid, error_message)
    """
    if not phone:
        return False, "Phone number is required"
    
    # Remove any non-digit characters for validation
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if we have a reasonable number of digits (7-15 is common internationally)
    if len(digits_only) < 7 or len(digits_only) > 15:
        return False, "Phone number must be between 7 and 15 digits"
    
    return True, ""

def validate_url(url):
    """
    Validate a URL format.
    Returns (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    # Simple URL validation regex
    url_pattern = re.compile(
        r'^(?:http|https)://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if url_pattern.match(url):
        return True, ""
    else:
        return False, "Invalid URL format"
