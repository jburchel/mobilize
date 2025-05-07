"""Database logging utilities for SQLAlchemy."""

from flask import current_app, g
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import re
from app.utils.log_utils import log_database_event


def extract_table_name(query):
    """Extract the table name from a SQL query.
    
    Args:
        query (str): The SQL query
        
    Returns:
        str: The extracted table name or 'unknown' if not found
    """
    # Common SQL operations and their table name patterns
    patterns = {
        'SELECT': r'\bFROM\s+([\w_\.]+)',
        'INSERT': r'\bINTO\s+([\w_\.]+)',
        'UPDATE': r'\bUPDATE\s+([\w_\.]+)',
        'DELETE': r'\bFROM\s+([\w_\.]+)',
        'CREATE': r'\bCREATE\s+(?:TABLE|INDEX)\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w_\.]+)',
        'DROP': r'\bDROP\s+(?:TABLE|INDEX)\s+(?:IF\s+EXISTS\s+)?([\w_\.]+)',
        'ALTER': r'\bALTER\s+TABLE\s+([\w_\.]+)'
    }
    
    # Determine operation type
    operation = query.strip().split(' ')[0].upper()
    
    # Try to extract table name based on operation
    if operation in patterns:
        match = re.search(patterns[operation], query, re.IGNORECASE)
        if match:
            return match.group(1).strip('`[]"')
    
    # If we can't determine the table, try a more generic approach
    generic_pattern = r'(?:FROM|INTO|UPDATE|TABLE)\s+([\w_\.]+)'
    match = re.search(generic_pattern, query, re.IGNORECASE)
    if match:
        return match.group(1).strip('`[]"')
    
    return 'unknown'


def determine_operation(query):
    """Determine the operation type from a SQL query.
    
    Args:
        query (str): The SQL query
        
    Returns:
        str: The operation type (SELECT, INSERT, UPDATE, DELETE, etc.)
    """
    first_word = query.strip().split(' ')[0].upper()
    
    # Map common SQL operations
    operations = {
        'SELECT': 'SELECT',
        'INSERT': 'INSERT',
        'UPDATE': 'UPDATE',
        'DELETE': 'DELETE',
        'CREATE': 'CREATE',
        'DROP': 'DROP',
        'ALTER': 'ALTER',
        'TRUNCATE': 'TRUNCATE',
        'GRANT': 'GRANT',
        'REVOKE': 'REVOKE',
        'COMMIT': 'COMMIT',
        'ROLLBACK': 'ROLLBACK',
        'BEGIN': 'BEGIN',
        'SET': 'SET',
        'SHOW': 'SHOW',
        'EXPLAIN': 'EXPLAIN'
    }
    
    return operations.get(first_word, 'OTHER')


def setup_db_logger(app, engine):
    """Set up database query logging.
    
    Args:
        app: Flask application instance
        engine: SQLAlchemy engine instance
    """
    @event.listens_for(engine, 'before_cursor_execute')
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        # Store the start time in the connection info
        conn.info.setdefault('query_start_time', [])
        conn.info['query_start_time'].append(time.time())
        
        # Store the statement for later use
        conn.info.setdefault('statements', [])
        conn.info['statements'].append(statement)
    
    @event.listens_for(engine, 'after_cursor_execute')
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        # Calculate query execution time
        if 'query_start_time' in conn.info and conn.info['query_start_time']:
            start_time = conn.info['query_start_time'].pop()
            
            # Get the statement
            if 'statements' in conn.info and conn.info['statements']:
                statement = conn.info['statements'].pop()
            
            # Calculate execution time in milliseconds
            execution_time = int((time.time() - start_time) * 1000)
            
            # Determine operation type and table name
            operation = determine_operation(statement)
            table = extract_table_name(statement)
            
            # Determine status based on execution time
            status = 'success'
            if execution_time > 1000:  # More than 1 second is considered slow
                status = 'slow'
            
            # Get user information if available
            user = None
            if hasattr(g, 'user') and g.user:
                user = g.user.email
            elif hasattr(g, 'current_user') and g.current_user and hasattr(g.current_user, 'email'):
                user = g.current_user.email
            
            # Get records affected
            records_affected = 0
            if hasattr(cursor, 'rowcount'):
                records_affected = cursor.rowcount
            
            # Log the database event
            try:
                log_database_event(
                    operation=operation,
                    table=table,
                    status=status,
                    duration=execution_time,
                    user=user,
                    records_affected=records_affected,
                    query=statement
                )
            except Exception as e:
                current_app.logger.error(f"Error logging database event: {str(e)}")


def init_app(app):
    """Initialize database logging.
    
    Args:
        app: Flask application instance
    """
    from app.extensions import db
    
    with app.app_context():
        setup_db_logger(app, db.engine)
        app.logger.info("Database query logging initialized")
