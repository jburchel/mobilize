from datetime import datetime, timezone

def format_date(date_obj, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Format a datetime object into a string.
    
    Args:
        date_obj: Datetime object to format
        format_str: String format to use (default: '%Y-%m-%d %H:%M:%S')
        
    Returns:
        Formatted date string
    """
    if not date_obj:
        return ''
        
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return date_obj
    
    # Ensure datetime has timezone info
    if date_obj.tzinfo is None:
        date_obj = date_obj.replace(tzinfo=timezone.utc)
        
    return date_obj.strftime(format_str) 