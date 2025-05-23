"""Template filters and functions for the application."""

from datetime import datetime
from markupsafe import Markup
import re
from .utilities import format_date, format_phone

def register_filters(app):
    """Register custom Jinja2 filters with the Flask application."""
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['date'] = format_date_filter
    app.jinja_env.filters['phone'] = format_phone_filter
    app.jinja_env.filters['truncate_html'] = truncate_html
    app.jinja_env.filters['initials'] = get_initials
    app.jinja_env.filters['status_class'] = status_class
    app.jinja_env.filters['nl2br'] = nl2br
    app.jinja_env.filters['format_location'] = format_location
    
def register_template_functions(app):
    """Register custom Jinja2 functions with the Flask application."""
    app.jinja_env.globals.update(dict(
        current_year=lambda: datetime.now().year,
        format_date=format_date,
        format_phone=format_phone,
        isinstance=isinstance,
        list=list,
        str=str,
        int=int,
        float=float,
        len=len,
        min=min,
        max=max,
        sum=sum,
        sorted=sorted,
        zip=zip,
        dict=dict,
        enumerate=enumerate,
        getattr=getattr,
        hasattr=hasattr
    ))

def format_datetime(value, format='%Y-%m-%d %H:%M'):
    """Format a datetime object to a string."""
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(format)

def format_date_filter(value, format='%Y-%m-%d'):
    """Format a date object to a string."""
    return format_date(value, format)

def format_phone_filter(value):
    """Format a phone number for display."""
    return format_phone(value)

def truncate_html(value, length=100, killwords=False, end='...'):
    """Truncate HTML string and preserve formatting."""
    if not value:
        return ''
    if len(value) <= length:
        return value
        
    # Extract text content
    text = re.sub(r'<[^>]*>', '', value)
    
    if killwords:
        # Cut at exact length
        text = text[:length]
    else:
        # Cut at word boundary
        text = text[:length].rsplit(' ', 1)[0]
        
    return text + end

def format_location(church):
    """Format location based on church city, state, and country.
    
    For US: City, State
    For Canada: City, Province
    For others: City, Country
    """
    if not church:
        return ''
    
    # If location is already provided, use it
    if getattr(church, 'location', None):
        return church.location
    
    city = getattr(church, 'city', '')
    state = getattr(church, 'state', '')
    country = getattr(church, 'country', '')
    
    if not city:
        return ''
    
    # For US addresses
    if country == 'United States' or country == 'USA' or country == 'US' or not country:
        if state:
            return f"{city}, {state}"
        return city
    
    # For Canadian addresses
    if country == 'Canada' or country == 'CA':
        if state:  # In this case, state field contains the province
            return f"{city}, {state}"
        return city
    
    # For all other countries
    return f"{city}, {country}" if country else city

def get_initials(value):
    """Get initials from a name."""
    if not value:
        return ''
    # Split name and take first letter of each part
    return ''.join(word[0].upper() for word in value.split() if word)

def status_class(status):
    """Return Bootstrap class based on status."""
    status_map = {
        'completed': 'success',
        'in_progress': 'info',
        'pending': 'warning',
        'failed': 'danger',
        'cancelled': 'secondary',
        'scheduled': 'primary',
        'partial': 'warning',
    }
    return status_map.get(status.lower(), 'secondary')

def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if not value:
        return ''
    # Replace newlines with HTML line breaks
    value = value.replace('\n', '<br>')
    # Mark the result as safe HTML to prevent escaping
    return Markup(value) 