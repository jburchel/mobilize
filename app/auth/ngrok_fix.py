"""Temporary fix for ngrok OAuth redirects and Cloud Run OAuth redirects."""

from flask import request

def get_oauth_redirect_uri():
    """
    Get the OAuth redirect URI, handling ngrok URLs and Cloud Run URLs properly.
    
    When running behind ngrok or on Cloud Run, the normal url_for with _external=True
    may not correctly detect the URL. This function provides a fix.
    """
    from flask import url_for, current_app
    import os
    
    # Get the host from the request headers
    host = request.headers.get('Host', '')
    scheme = request.headers.get('X-Forwarded-Proto', 'https')
    
    # Log the host and scheme for debugging
    current_app.logger.info(f"OAuth Redirect - Host: {host}, Scheme: {scheme}")
    
    # Check if we're running behind ngrok
    if 'ngrok' in host:
        redirect_uri = f"{scheme}://{host}/api/auth/google/callback"
        current_app.logger.info(f"Using ngrok redirect URI: {redirect_uri}")
        return redirect_uri
    
    # Check if we're running on Cloud Run
    if 'run.app' in host:
        redirect_uri = f"https://{host}/api/auth/google/callback"
        current_app.logger.info(f"Using Cloud Run redirect URI: {redirect_uri}")
        return redirect_uri
    
    # For production with custom domain or local development, use the BASE_URL from environment variables
    base_url = os.environ.get('BASE_URL') or current_app.config.get('BASE_URL')
    if base_url:
        redirect_uri = f"{base_url}/api/auth/google/callback"
        current_app.logger.info(f"Using BASE_URL redirect URI: {redirect_uri}")
        return redirect_uri
    
    # Fallback to Flask's url_for
    redirect_uri = url_for('auth.oauth2callback', _external=True)
    current_app.logger.info(f"Using fallback redirect URI: {redirect_uri}")
    return redirect_uri