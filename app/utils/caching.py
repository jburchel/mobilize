"""Caching utilities for the Mobilize app.

This module provides caching functions for frequently accessed data
to improve page load times in production.
"""

# current_app is imported within functions to avoid circular imports
from app.extensions import cache, db
from app.models.person import Person
from app.models.church import Church
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from sqlalchemy import text
import time
import logging

logger = logging.getLogger(__name__)

# Cache timeouts (in seconds)
SHORT_TIMEOUT = 60  # 1 minute
MEDIUM_TIMEOUT = 300  # 5 minutes
LONG_TIMEOUT = 1800  # 30 minutes


def init_app(app):
    """Initialize caching for the application."""
    # Only enable caching in production
    is_production = app.config.get('ENV') == 'production' or app.config.get('FLASK_ENV') == 'production'
    if not is_production and not app.config.get('FORCE_CACHING'):
        app.logger.info("Caching disabled in development environment")
        return
    
    app.logger.info("Initializing data caching for improved performance")
    
    # Register cache invalidation hooks
    register_cache_invalidation(app)
    
    app.logger.info("Caching initialized successfully")


def register_cache_invalidation(app):
    """Register hooks to invalidate cache when data changes."""
    from sqlalchemy import event
    from app.models.person import Person
    from app.models.church import Church
    from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
    
    # Invalidate people cache when a person is added/modified/deleted
    for operation in ('after_insert', 'after_update', 'after_delete'):
        event.listen(Person, operation, lambda mapper, connection, target: invalidate_people_cache())
    
    # Invalidate churches cache when a church is added/modified/deleted
    for operation in ('after_insert', 'after_update', 'after_delete'):
        event.listen(Church, operation, lambda mapper, connection, target: invalidate_churches_cache())
    
    # Invalidate pipeline cache when pipeline data changes
    for model in (Pipeline, PipelineStage, PipelineContact):
        for operation in ('after_insert', 'after_update', 'after_delete'):
            event.listen(model, operation, lambda mapper, connection, target: invalidate_pipeline_cache())
    
    app.logger.info("Cache invalidation hooks registered")


# Cache invalidation functions
def invalidate_people_cache():
    """Invalidate all people-related cache entries."""
    logger.info("Invalidating people cache")
    cache.delete_many('people_*')


def invalidate_churches_cache():
    """Invalidate all churches-related cache entries."""
    logger.info("Invalidating churches cache")
    cache.delete_many('churches_*')
    cache.delete_many('church_*')
    cache.delete_many('churches_search_*')
    logger.info("Churches cache invalidated")


def invalidate_pipeline_cache():
    """Invalidate all pipeline-related caches."""
    cache.delete_many('pipeline_*')
    cache.delete_many('person_pipeline_*')
    cache.delete_many('church_pipeline_*')
    logger.info("Pipeline cache invalidated")


# People caching functions
def get_cached_people(office_id=None, page=1, per_page=20, search_query=None):
    """Get a cached list of people with pagination."""
    from flask import current_app
    
    # Skip caching in development
    if current_app.config.get('ENV') == 'development' and not current_app.config.get('FORCE_CACHING'):
        return _get_people_data(office_id, page, per_page, search_query)
    
    # Create a cache key based on parameters
    cache_key = f"people_list_{office_id}_{page}_{per_page}_{search_query}"
    
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return cached_data
    
    # If not in cache, fetch from database
    logger.info(f"Cache miss for {cache_key}, fetching from database")
    start_time = time.time()
    result = _get_people_data(office_id, page, per_page, search_query)
    
    # Cache the result, but handle serialization errors
    try:
        cache.set(cache_key, result, timeout=MEDIUM_TIMEOUT)
        logger.info(f"Cached {len(result.get('people', []))} people in {time.time() - start_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to cache people data: {str(e)}")
        # Continue without caching
    
    return result


def _get_people_data(office_id=None, page=1, per_page=20, search_query=None):
    """Get list of people with pagination and optional filtering."""
    # Create base query
    query = Person.query
    
    # Filter by office if specified
    if office_id:
        query = query.filter_by(office_id=office_id)
    
    # Apply search filter if provided
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Person.first_name.ilike(search_term),
                Person.last_name.ilike(search_term),
                Person.email.ilike(search_term),
                Person.phone.ilike(search_term)
            )
        )
    
    # Using pagination to limit the number of records fetched
    pagination = query.order_by(Person.last_name, Person.first_name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    people = pagination.items
    
    # Get pipeline stages for all people in the current page using a single query
    person_ids = [p.id for p in people]
    
    # Use optimized query to get pipeline stages
    pipeline_stages = {}
    if person_ids:
        # Get the main pipeline for proper pipeline stages
        main_pipeline = Pipeline.query.filter(
            Pipeline.is_main_pipeline,
            Pipeline.pipeline_type.in_(['person', 'people'])
        ).first()
        
        if main_pipeline:
            # Use a single query to get all pipeline stages
            pipeline_contacts = db.session.execute(
                text("""
                    SELECT pc.contact_id, ps.name 
                    FROM pipeline_contacts pc
                    JOIN pipeline_stages ps ON pc.current_stage_id = ps.id
                    WHERE pc.contact_id IN :person_ids
                    AND pc.pipeline_id = :pipeline_id
                """),
                {"person_ids": tuple(person_ids) if len(person_ids) > 1 else (person_ids[0],), 
                 "pipeline_id": main_pipeline.id}
            ).fetchall()
            
            # Create a mapping of person_id to pipeline stage
            for pc in pipeline_contacts:
                pipeline_stages[pc[0]] = pc[1]
    
    # Attach pipeline stage to each person object
    for person in people:
        person.current_pipeline_stage = pipeline_stages.get(person.id, 'Not in Pipeline')
    
    # Create result dictionary
    result = {
        'people': people,
        'pagination': pagination,
        'total': pagination.total
    }
    
    # Cache the result, but handle serialization errors
    try:
        cache.set(cache_key, result, timeout=MEDIUM_TIMEOUT)
        logger.info(f"Cached {len(result.get('people', []))} people in {time.time() - start_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to cache people data: {str(e)}")
        # Continue without caching
    
    return result


def get_cached_person(person_id):
    """Get a cached person by ID with related data."""
    from flask import current_app
    
    # Skip caching in development
    if current_app.config.get('ENV') == 'development' and not current_app.config.get('FORCE_CACHING'):
        return _get_person_data(person_id)
        
    cache_key = f"person_{person_id}"
    
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return cached_data
    
    logger.info(f"Cache miss for {cache_key}, fetching from database")
    start_time = time.time()
    
    result = _get_person_data(person_id)
    
    # Cache the result, but handle serialization errors
    try:
        cache.set(cache_key, result, timeout=MEDIUM_TIMEOUT)
        logger.info(f"Cached person data in {time.time() - start_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to cache person data: {str(e)}")
        # Continue without caching
    
    return result


def _get_person_data(person_id):
    """Get a person by ID with related data."""
    # Get person with related data
    person = Person.query.get(person_id)
    if not person:
        return None
    
    # Get communications for this person
    from app.models.communication import Communication
    communications = Communication.query.filter_by(person_id=person.id).order_by(db.desc(Communication.date_sent)).limit(10).all()
    
    # Get tasks for this person
    from app.models.task import Task
    tasks = Task.query.filter_by(person_id=person.id).order_by(db.desc(Task.due_date)).limit(10).all()
    
    # Get pipeline information
    pipeline_info = None
    main_pipeline = Pipeline.query.filter(
        Pipeline.is_main_pipeline,
        Pipeline.pipeline_type.in_(['person', 'people'])
    ).first()
    
    if main_pipeline:
        pipeline_contact = PipelineContact.query.filter_by(
            contact_id=person.id,
            pipeline_id=main_pipeline.id
        ).first()
        
        if pipeline_contact and pipeline_contact.current_stage:
            pipeline_info = {
                'pipeline': main_pipeline,
                'stage': pipeline_contact.current_stage.name,
                'entered_at': pipeline_contact.entered_at
            }
    
    # Create result dictionary
    result = {
        'person': person,
        'communications': communications,
        'tasks': tasks,
        'pipeline_info': pipeline_info
    }
    
    # No need to cache here as it's already handled in get_cached_person
    # The caching logic should only be in the wrapper function, not here
    
    return result


# Churches caching functions
def get_cached_churches(office_id=None, page=1, per_page=20, search_query=None):
    """Get cached list of churches with pagination and optional filtering."""
    # Create a cache key based on parameters
    cache_key = f"churches_list_{office_id}_{page}_{per_page}"
    if search_query:
        # Include search in cache key but hash it to avoid invalid characters
        import hashlib
        search_hash = hashlib.md5(search_query.encode()).hexdigest()
        cache_key = f"churches_search_{search_hash}_{office_id}_{page}_{per_page}"
    
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return cached_data
    
    logger.info(f"Cache miss for {cache_key}, fetching from database")
    start_time = time.time()
    
    # Create base query
    query = Church.query
    
    # Filter by office if specified
    if office_id:
        query = query.filter_by(office_id=office_id)
    
    # Apply search filter if provided
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Church.name.ilike(search_term),
                Church.email.ilike(search_term),
                Church.phone.ilike(search_term),
                Church.address.ilike(search_term),
                Church.city.ilike(search_term)
            )
        )
    
    # Using pagination to limit the number of records fetched
    pagination = query.order_by(Church.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    churches = pagination.items
    
    # Get pipeline stages for all churches in the current page using a single query
    church_ids = [c.id for c in churches]
    
    # Use optimized query to get pipeline stages
    pipeline_stages = {}
    if church_ids:
        # Get the main pipeline for proper pipeline stages
        main_pipeline = Pipeline.query.filter(
            Pipeline.is_main_pipeline,
            Pipeline.pipeline_type == 'church'
        ).first()
        
        if main_pipeline:
            # Use a single query to get all pipeline stages
            pipeline_contacts = db.session.execute(
                text("""
                    SELECT pc.contact_id, ps.name 
                    FROM pipeline_contacts pc
                    JOIN pipeline_stages ps ON pc.current_stage_id = ps.id
                    WHERE pc.contact_id IN :church_ids
                    AND pc.pipeline_id = :pipeline_id
                """),
                {"church_ids": tuple(church_ids) if len(church_ids) > 1 else (church_ids[0],), 
                 "pipeline_id": main_pipeline.id}
            ).fetchall()
            
            # Create a mapping of church_id to pipeline stage
            for pc in pipeline_contacts:
                pipeline_stages[pc[0]] = pc[1]
    
    # Attach pipeline stage to each church object
    for church in churches:
        church.current_pipeline_stage = pipeline_stages.get(church.id, 'Not in Pipeline')
    
    # Create result dictionary
    result = {
        'churches': churches,
        'pagination': pagination,
        'total': pagination.total
    }
    
    # Cache the result
    cache.set(cache_key, result, timeout=MEDIUM_TIMEOUT)
    
    logger.info(f"Cached {len(churches)} churches in {time.time() - start_time:.2f}s")
    return result


def get_cached_church(church_id):
    """Get a cached church by ID with related data."""
    cache_key = f"church_{church_id}"
    
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return cached_data
    
    logger.info(f"Cache miss for {cache_key}, fetching from database")
    start_time = time.time()
    
    # Get church with related data
    church = Church.query.get(church_id)
    if not church:
        return None
    
    # Get communications for this church
    from app.models.communication import Communication
    communications = Communication.query.filter_by(church_id=church.id).order_by(db.desc(Communication.date_sent)).limit(10).all()
    
    # Get tasks for this church
    from app.models.task import Task
    tasks = Task.query.filter_by(church_id=church.id).order_by(db.desc(Task.due_date)).limit(10).all()
    
    # Get members (people) for this church
    members = Person.query.filter_by(church_id=church_id).all()
    
    # Get pipeline information
    pipeline_info = None
    main_pipeline = Pipeline.query.filter(
        Pipeline.is_main_pipeline,
        Pipeline.pipeline_type == 'church'
    ).first()
    
    if main_pipeline:
        pipeline_contact = PipelineContact.query.filter_by(
            contact_id=church.id,
            pipeline_id=main_pipeline.id
        ).first()
        
        if pipeline_contact and pipeline_contact.current_stage:
            pipeline_info = {
                'pipeline': main_pipeline,
                'stage': pipeline_contact.current_stage.name,
                'entered_at': pipeline_contact.entered_at
            }
    
    # Create result dictionary
    result = {
        'church': church,
        'communications': communications,
        'tasks': tasks,
        'members': members,
        'pipeline_info': pipeline_info
    }
    
    # Cache the result
    cache.set(cache_key, result, timeout=MEDIUM_TIMEOUT)
    
    logger.info(f"Cached church {church_id} in {time.time() - start_time:.2f}s")
    return result


# Pipeline caching functions
def get_cached_pipeline(pipeline_id=None, pipeline_type=None):
    """Get cached pipeline data by ID or type."""
    # Determine cache key based on provided parameters
    if pipeline_id:
        cache_key = f"pipeline_{pipeline_id}"
    elif pipeline_type:
        cache_key = f"pipeline_type_{pipeline_type}"
    else:
        return None
    
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return cached_data
    
    logger.info(f"Cache miss for {cache_key}, fetching from database")
    start_time = time.time()
    
    # Get pipeline data
    pipeline = None
    if pipeline_id:
        pipeline = Pipeline.query.get(pipeline_id)
    elif pipeline_type:
        pipeline = Pipeline.query.filter(
            Pipeline.is_main_pipeline,
            Pipeline.pipeline_type == pipeline_type
        ).first()
    
    if not pipeline:
        return None
    
    # Get pipeline stages
    stages = PipelineStage.query.filter_by(pipeline_id=pipeline.id).order_by(PipelineStage.order).all()
    
    # Get contacts in each stage using a single optimized query
    contacts_by_stage = {stage.id: [] for stage in stages}
    
    # Use direct SQL for better performance
    contacts_query = db.session.execute(
        text("""
            SELECT pc.id, pc.contact_id, pc.current_stage_id, pc.entered_at, pc.last_updated,
                   c.type as contact_type, c.name as contact_name,
                   CASE c.type 
                       WHEN 'person' THEN p.first_name || ' ' || p.last_name
                       WHEN 'church' THEN ch.name
                       ELSE c.name
                   END as display_name
            FROM pipeline_contacts pc
            JOIN contacts c ON pc.contact_id = c.id
            LEFT JOIN people p ON c.id = p.id AND c.type = 'person'
            LEFT JOIN churches ch ON c.id = ch.id AND c.type = 'church'
            WHERE pc.pipeline_id = :pipeline_id
        """),
        {"pipeline_id": pipeline.id}
    ).fetchall()
    
    # Process the results
    for row in contacts_query:
        # Create a lightweight contact object with just the needed attributes
        contact = {
            'id': row[0],
            'contact_id': row[1],
            'current_stage_id': row[2],
            'entered_at': row[3],
            'last_updated': row[4],
            'contact_type': row[5],
            'display_name': row[7]
        }
        
        # Add to the appropriate stage
        if row[2] in contacts_by_stage:
            contacts_by_stage[row[2]].append(contact)
    
    # Create result dictionary
    result = {
        'pipeline': pipeline,
        'stages': stages,
        'contacts_by_stage': contacts_by_stage
    }
    
    # Cache the result
    cache.set(cache_key, result, timeout=MEDIUM_TIMEOUT)
    
    total_contacts = sum(len(contacts) for contacts in contacts_by_stage.values())
    logger.info(f"Cached pipeline {pipeline.id} with {len(stages)} stages and {total_contacts} contacts in {time.time() - start_time:.2f}s")
    return result
