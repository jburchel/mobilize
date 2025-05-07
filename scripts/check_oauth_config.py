#!/usr/bin/env python3

"""
Script to check and display Google OAuth configuration.
This will help diagnose the 'Access blocked: Authorization Error' issue.
"""

import os
import json
from urllib.parse import urlparse

def check_oauth_config():
    """Check and display the current OAuth configuration."""
    print("\n=== Google OAuth Configuration Checker ===")
    
    # Check environment variables
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("\n❌ ERROR: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET environment variables are not set!")
        print("   These must be set for OAuth to work properly.")
    else:
        print(f"\n✅ GOOGLE_CLIENT_ID is set: {client_id[:10]}...")
        print(f"✅ GOOGLE_CLIENT_SECRET is set: {client_secret[:5]}...")
    
    # Check Firebase credentials
    firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
    if not firebase_creds_json:
        print("\n❌ WARNING: FIREBASE_CREDENTIALS environment variable is not set!")
    else:
        try:
            firebase_creds = json.loads(firebase_creds_json)
            project_id = firebase_creds.get('project_id')
            print(f"\n✅ Firebase project ID: {project_id}")
        except Exception as e:
            print(f"\n❌ ERROR parsing FIREBASE_CREDENTIALS: {str(e)}")
    
    # Display current URLs that need to be in the OAuth configuration
    print("\n=== Required Redirect URIs ===")
    print("The following URLs must be added as authorized redirect URIs in your Google Cloud Console:")
    print("https://mobilize-crm-1069318103780.us-central1.run.app/api/auth/google/callback")
    print("https://mobilize-crm.org/api/auth/google/callback")
    
    # Instructions for fixing
    print("\n=== How to Fix 'Access blocked: Authorization Error' ===")
    print("1. Go to the Google Cloud Console: https://console.cloud.google.com/apis/credentials")
    if client_id:
        # Extract the client number from the client ID
        client_number = client_id.split('.')[0]
        print(f"2. Find and edit the OAuth 2.0 Client ID: {client_number}")
    else:
        print("2. Find and edit your OAuth 2.0 Client ID")
    print("3. Under 'Authorized redirect URIs', add both URLs listed above")
    print("4. Click 'Save' and wait a few minutes for changes to propagate")
    print("5. Try signing in again")
    
    print("\nNote: If you're still having issues, make sure your application is using HTTPS")
    print("and that the domain you're accessing matches one of the authorized redirect URIs.")

if __name__ == "__main__":
    check_oauth_config()
