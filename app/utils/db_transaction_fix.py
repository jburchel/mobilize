"""Database transaction fix for SQLAlchemy.

This module adds request handlers to automatically rollback aborted transactions.
"""

from flask import g
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text # Add this import
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

def init_app(app):
    """Initialize the database transaction fix."""
    # Monkey patch SQLAlchemy session to handle transaction errors
    original_execute = db.session.execute
    
    def patched_execute(statement, *args, **kwargs):
        try:
            return original_execute(statement, *args, **kwargs)
        except SQLAlchemyError as e:
            error_str = str(e)
            # Handle a wider range of transaction errors
            if any(err in error_str for err in [
                'InFailedSqlTransaction', 
                'current transaction is aborted', 
                'operator does not exist',
                'No operator matches',
                'could not complete cursor operation'
            ]):
                logger.warning(f"Caught transaction error: {error_str}, attempting recovery")
                try:
                    # Force rollback the current transaction
                    db.session.rollback()
                    logger.info("Successfully rolled back transaction")
                    
                    # Try a simple query to verify the connection is working
                    try:
                        db.session.execute(text("SELECT 1"))
                        logger.info("Database connection verified after rollback")
                    except Exception as verify_error:
                        logger.error(f"Connection still broken after rollback: {str(verify_error)}")
                        # Create a completely new session
                        db.session.remove()
                        db.session = db.create_scoped_session()
                        logger.info("Created new database session after failed verification")
                    
                    # Try again after recovery
                    return original_execute(statement, *args, **kwargs)
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {str(rollback_error)}")
                    # Create a new session as a last resort
                    db.session.remove()
                    db.session = db.create_scoped_session()
                    logger.info("Created new database session")
                    # Try once more with the new session
                    return db.session.execute(statement, *args, **kwargs)
            else:
                # Re-raise other SQLAlchemy errors
                raise
    
    # Replace the execute method with our patched version
    db.session.execute = patched_execute
    
    @app.before_request
    def ensure_db_session():
        """Ensure a fresh database session at the start of each request."""
        # Store the original session on the g object for reference
        g.original_db_session = db.session
        
        # Always start with a clean session for each request
        try:
            # Close any existing session first
            db.session.close()
            
            # Check if we need to rollback any existing transaction
            try:
                # Try a simple query to check if the session is usable
                db.session.execute(text("SELECT 1"))
                logger.debug("Database session verified at request start")
            except SQLAlchemyError as e:
                logger.warning(f"Database session error detected, rolling back: {str(e)}")
                try:
                    db.session.rollback()
                    logger.info("Successfully rolled back transaction")
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {str(rollback_error)}")
                    # Create a new session as a last resort
                    db.session.remove()
                    db.session = db.create_scoped_session()
                    logger.info("Created new database session")
        except Exception as session_error:
            logger.error(f"Error setting up session: {str(session_error)}")
            # Create a completely new session
            db.session.remove()
            db.session = db.create_scoped_session()
            logger.info("Created new database session after setup error")
    
    @app.teardown_request
    def cleanup_db_session(exception=None):
        """Clean up the database session at the end of each request."""
        if exception:
            logger.warning(f"Exception during request, rolling back transaction: {str(exception)}")
            try:
                db.session.rollback()
            except Exception as e:
                logger.error(f"Error during rollback in teardown: {str(e)}")
        
        # Always close the session at the end of the request
        try:
            db.session.close()
        except Exception as e:
            logger.error(f"Error closing session: {str(e)}")
