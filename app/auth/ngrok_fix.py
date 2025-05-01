"""Temporary fix for ngrok OAuth redirects and Cloud Run OAuth redirects."""

from flask import request

def get_oauth_redirect_uri():
    """
    Get the OAuth redirect URI, handling ngrok URLs and Cloud Run URLs properly.
    
    When running behind ngrok or on Cloud Run, the normal url_for with _external=True
    may not correctly detect the URL. This function provides a fix.
    """
    # Get the host from the request headers
    host = request.headers.get('Host', '')
    scheme = request.headers.get('X-Forwarded-Proto', 'https')
    
    # Check if we're running behind ngrok
    if 'ngrok' in host:
        return f"{scheme}://{host}/api/auth/google/callback"
    
    # Check if we're running on Cloud Run
    if 'run.app' in host:
        return f"https://{host}/api/auth/google/callback"
    
    # Not running behind ngrok or Cloud Run, let Flask handle it normally
    from flask import url_for
    return url_for('auth.oauth2callback', _external=True) 