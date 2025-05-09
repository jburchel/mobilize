"""Church caching utilities for the Mobilize app.

This module provides caching functions for church data
to improve page load times in production.
"""

from app.extensions import cache
from app.models.church import Church
import time
import logging

logger = logging.getLogger(__name__)

# Cache timeouts (in seconds)
SHORT_TIMEOUT = 60  # 1 minute
MEDIUM_TIMEOUT = 300  # 5 minutes
LONG_TIMEOUT = 1800  # 30 minutes


def get_cached_churches(office_id=None, page=1, per_page=50, search_query=None):
    """Get a cached list of churches with pagination."""
    from flask import current_app
    
    # Skip caching in development
    if current_app.config.get('ENV') == 'development' and not current_app.config.get('FORCE_CACHING'):
        return _get_churches_data(office_id, page, per_page, search_query)
    
    # Create a cache key based on parameters
    cache_key = f"churches_list_{office_id}_{page}_{per_page}_{search_query}"
    
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return cached_data
    
    # If not in cache, fetch from database
    logger.info(f"Cache miss for {cache_key}, fetching from database")
    start_time = time.time()
    result = _get_churches_data(office_id, page, per_page, search_query)
    
    # Cache the result, but handle serialization errors
    try:
        cache.set(cache_key, result, timeout=MEDIUM_TIMEOUT)
        logger.info(f"Cached {len(result.get('churches', []))} churches in {time.time() - start_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to cache churches data: {str(e)}")
        # Continue without caching
    
    return result


def _get_churches_data(office_id=None, page=1, per_page=50, search_query=None):
    """Get list of churches with pagination and optional filtering."""
    # Create base query
    query = Church.query
    
    # Filter by office if specified
    if office_id:
        query = query.filter(Church.office_id == office_id)
    
    # Apply search filter if specified
    if search_query:
        search_terms = search_query.split()
        for term in search_terms:
            search_filter = (
                Church.name.ilike(f'%{term}%') |
                Church.address.ilike(f'%{term}%') |
                Church.city.ilike(f'%{term}%') |
                Church.state.ilike(f'%{term}%') |
                Church.zip_code.ilike(f'%{term}%')
            )
            query = query.filter(search_filter)
    
    # Order by name
    query = query.order_by(Church.name)
    
    # Paginate the results
    pagination = query.paginate(page=page, per_page=per_page)
    churches = pagination.items
    
    # Format the results
    result = {
        'churches': churches,  # Return Church objects for template rendering
        'pagination': pagination,
        'total': pagination.total,
        'raw_data': [  # Include raw data for API/chart compatibility
            {
                'id': church.id,
                'name': church.name,
                'address': church.address,
                'city': church.city,
                'state': church.state,
                'zip_code': church.zip_code,
                'created_at': church.created_at.isoformat() if church.created_at else None,
                'updated_at': church.updated_at.isoformat() if church.updated_at else None
            } for church in churches
        ]
    }
    
    return result
