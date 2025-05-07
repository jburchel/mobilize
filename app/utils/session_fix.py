import logging
from flask_login import current_user, user_loaded_from_request, login_user
from flask import session, g, request
from sqlalchemy.orm.exc import DetachedInstanceError
from app.extensions import db

logger = logging.getLogger(__name__)

def init_app(app):
    """
    Initialize session fixes for the application.
    This adds request handlers to ensure user objects are properly attached to sessions.
    """
    @app.before_request
    def ensure_user_session():
        """
        Ensure the current_user is attached to the current session if it exists.
        This prevents DetachedInstanceError when accessing user attributes.
        """
        # Skip for static files and certain paths
        if request.path.startswith('/static/') or request.path.startswith('/favicon.ico'):
            return
            
        try:
            # First check if we have a user ID in the session
            user_id = session.get('_user_id')
            
            # If we have a user ID but current_user is not authenticated or detached
            if user_id:
                try:
                    # Try to access current_user to see if it's properly attached
                    if current_user and current_user.is_authenticated:
                        # Try to access an attribute to check for detachment
                        try:
                            _ = current_user.id  # This will raise DetachedInstanceError if detached
                        except DetachedInstanceError:
                            # User is detached, need to refresh
                            logger.warning(f"User {user_id} is detached, refreshing")
                            from app.models.user import User
                            fresh_user = User.query.get(user_id)
                            if fresh_user:
                                # Re-login the user with the fresh object
                                login_user(fresh_user, remember=True)
                                # Store in g for this request
                                g.fresh_user = fresh_user
                                logger.info(f"Re-logged in detached user {user_id}")
                except Exception as e:
                    logger.error(f"Error checking current_user: {str(e)}")
                    
                # Always try to get a fresh user regardless of the above
                try:
                    from app.models.user import User
                    fresh_user = User.query.get(user_id)
                    if fresh_user:
                        # Store the fresh user in the Flask g object for this request
                        g.fresh_user = fresh_user
                        # Make sure it's in the current session
                        db.session.add(fresh_user)
                        # Force update the _user_id in the flask_login session
                        session['_user_id'] = user_id
                        logger.info(f"User {user_id} refreshed and attached to session")
                except Exception as e:
                    logger.error(f"Error refreshing user {user_id}: {str(e)}")
                    
            # Handle OAuth callback paths specially
            elif '/api/auth/google/callback' in request.path:
                logger.info(f"Processing OAuth callback: {request.path}")
                # Don't do anything special, let the OAuth handler do its job
        except Exception as e:
            logger.error(f"Error in ensure_user_session: {str(e)}")
            # Don't raise the exception, just log it
            # This ensures the request can continue even if there's an issue

    @app.after_request
    def cleanup_session(response):
        """
        Clean up the session after each request.
        """
        # Handle server errors
        if response.status_code >= 500:
            # If there was a server error, rollback any uncommitted changes
            try:
                db.session.rollback()
                logger.info("Session rolled back due to server error")
            except Exception as e:
                logger.error(f"Error rolling back session: {str(e)}")
                
        # Handle authentication errors specifically
        if response.status_code == 401 or (response.status_code == 302 and '/api/auth/login' in response.location):
            # This might be an authentication issue, check if we need to clear the session
            try:
                if session.get('_user_id'):
                    # If we have a user ID but got redirected to login, there might be a session issue
                    logger.warning(f"Authentication issue detected for user {session.get('_user_id')}")
            except Exception as e:
                logger.error(f"Error handling auth error: {str(e)}")
                
        # Always commit any pending changes to avoid DetachedInstanceError
        try:
            if db.session.dirty or db.session.new or db.session.deleted:
                db.session.commit()
                logger.debug("Committed pending session changes")
        except Exception as e:
            logger.error(f"Error committing session: {str(e)}")
            try:
                db.session.rollback()
            except Exception as e2:
                logger.error(f"Error in rollback: {str(e2)}")
        
        # Clean up any request-specific objects
        if hasattr(g, 'fresh_user'):
            delattr(g, 'fresh_user')
        
        return response
        
    # Add a handler for when the user is loaded from the request
    @user_loaded_from_request.connect_via(app)
    def on_user_loaded(sender, user=None):
        """
        Handle when a user is loaded from the request.
        This ensures the user is properly attached to the session.
        """
        if user:
            try:
                # Store the user ID in the session explicitly
                user_id = user.get_id()
                if user_id:
                    session['_user_id'] = user_id
                    
                # Make sure the user is attached to the current session
                db.session.add(user)
                
                # Store in g for this request for easy access
                g.fresh_user = user
                
                # If this is an OAuth callback, ensure we commit the session
                if '/api/auth/google/callback' in request.path:
                    db.session.commit()
                    logger.info(f"User {user_id} committed to session during OAuth callback")
                else:
                    logger.info(f"User {user_id} attached to session on load")
            except Exception as e:
                logger.error(f"Error attaching user to session on load: {str(e)}")
                # Try to recover by refreshing the session
                try:
                    db.session.rollback()
                    # Try to get a fresh copy from the database
                    from app.models.user import User
                    user_id = user.get_id()
                    if user_id:
                        fresh_user = User.query.get(user_id)
                        if fresh_user:
                            # Re-login with the fresh user
                            login_user(fresh_user, remember=True)
                            g.fresh_user = fresh_user
                            logger.info(f"Recovered user {user_id} after error")
                except Exception as e2:
                    logger.error(f"Failed to recover user after error: {str(e2)}")
