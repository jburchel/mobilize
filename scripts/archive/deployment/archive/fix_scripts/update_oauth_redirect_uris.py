#!/usr/bin/env python3
import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def update_oauth_redirect_uris():
    """Update OAuth redirect URIs for the Google OAuth client."""
    try:
        # Get the client ID from environment variable
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not client_id:
            print("Error: GOOGLE_CLIENT_ID environment variable not set")
            sys.exit(1)
            
        # Extract the client ID without the .apps.googleusercontent.com suffix
        client_id_number = client_id.split('-')[0]
        
        print(f"Using client ID: {client_id}")
        
        # Define the redirect URIs we want to ensure are configured
        redirect_uris = [
            "https://mobilize-crm.org/api/auth/google/callback",
            "https://mobilize-crm-1069318103780.us-central1.run.app/api/auth/google/callback"
        ]
        
        print("\nTo update your Google OAuth client configuration, follow these steps:")
        print("\n1. Go to the Google Cloud Console: https://console.cloud.google.com/apis/credentials")
        print(f"\n2. Find and click on the OAuth client ID with client ID: {client_id}")
        print("\n3. Under 'Authorized redirect URIs', make sure the following URIs are added:")
        for uri in redirect_uris:
            print(f"   - {uri}")
        print("\n4. Click 'Save' to update the configuration")
        print("\nAfter updating the redirect URIs, try accessing the application again.")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = update_oauth_redirect_uris()
    if success:
        print("\nScript completed successfully")
    else:
        print("\nScript failed")
        sys.exit(1)
