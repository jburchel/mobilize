"""Query optimization utilities for the Flask application."""

from functools import wraps
from flask import current_app, request
from app.extensions import cache
from sqlalchemy import func
import time

def optimize_query(query, limit=None, offset=None):
    """Apply common optimizations to a SQLAlchemy query.
    
    Args:
        query: The SQLAlchemy query to optimize
        limit: Optional limit for the query results
        offset: Optional offset for pagination
        
    Returns:
        The optimized query object
    """
    # Apply limit and offset if provided
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
        
    return query

def with_pagination(query, page=1, per_page=20):
    """Apply pagination to a SQLAlchemy query.
    
    Args:
        query: The SQLAlchemy query to paginate
        page: The page number (1-indexed)
        per_page: Number of items per page
        
    Returns:
        Tuple of (items, pagination_info)
    """
    # Ensure page is at least 1
    page = max(1, page)
    
    # Get total count for pagination
    total = query.count()
    
    # Calculate pagination values
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    offset = (page - 1) * per_page
    
    # Apply pagination to query
    items = query.limit(per_page).offset(offset).all()
    
    # Create pagination info dictionary
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages,
        'has_next': page < pages,
        'has_prev': page > 1
    }
    
    return items, pagination

def cached_query(timeout=300):
    """Decorator to cache the result of a view function.
    
    This only applies caching in production environments.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip caching in development or testing
            if current_app.config.get('ENV') != 'production' and current_app.config.get('FLASK_ENV') != 'production':
                return f(*args, **kwargs)
            
            # Create a cache key based on the function name and request arguments
            cache_key = f"{f.__name__}:{request.path}:{str(request.args)}"
            
            # Try to get from cache
            response = cache.get(cache_key)
            if response is not None:
                return response
            
            # If not in cache, call the function and cache the result
            response = f(*args, **kwargs)
            cache.set(cache_key, response, timeout=timeout)
            
            return response
        return decorated_function
    return decorator
