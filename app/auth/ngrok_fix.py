"""Temporary fix for ngrok OAuth redirects."""

import os
from flask import request

def get_oauth_redirect_uri():
    """
    Get the OAuth redirect URI, handling ngrok URLs properly.
    
    When running behind ngrok, the normal url_for with _external=True
    may not correctly detect the ngrok URL. This function provides a fix.
    """
    # Check if we're running behind ngrok
    host = request.headers.get('Host', '')
    if 'ngrok' in host:
        scheme = request.headers.get('X-Forwarded-Proto', 'https')
        return f"{scheme}://{host}/auth/google/callback"
    
    # Not running behind ngrok, let Flask handle it normally
    from flask import url_for
    return url_for('auth.oauth2callback', _external=True) 