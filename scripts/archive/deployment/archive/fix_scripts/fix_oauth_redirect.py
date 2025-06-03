#!/usr/bin/env python3
import os
import sys
import requests

def check_and_fix_oauth_redirect():
    """Check and fix OAuth redirect URIs for both domains."""
    # Get the client ID and secret from environment variables
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET environment variable not set")
        sys.exit(1)
    
    # Define the redirect URIs we need to ensure are configured
    redirect_uris = [
        "https://mobilize-crm.org/api/auth/google/callback",
        "https://mobilize-crm-1069318103780.us-central1.run.app/api/auth/google/callback"
    ]
    
    # Check if the custom domain is correctly set in the BASE_URL environment variable
    base_url = os.getenv('BASE_URL')
    if not base_url or 'mobilize-crm.org' not in base_url:
        print(f"Warning: BASE_URL environment variable is not set correctly: {base_url}")
        print("It should be set to 'https://mobilize-crm.org'")
        print("\nInstructions to fix BASE_URL:")
        print("1. Go to the Google Cloud Console: https://console.cloud.google.com/run/detail/us-central1/mobilize-crm/revisions")
        print("2. Click on 'Edit & Deploy New Revision'")
        print("3. Go to the 'Variables & Secrets' tab")
        print("4. Add or update the BASE_URL environment variable to 'https://mobilize-crm.org'")
        print("5. Click 'Deploy'")
    else:
        print(f"BASE_URL is correctly set to: {base_url}")
    
    # Generate instructions for updating the OAuth client
    print("\nTo update your Google OAuth client configuration, follow these steps:")
    print("\n1. Go to the Google Cloud Console: https://console.cloud.google.com/apis/credentials")
    print(f"\n2. Find and click on the OAuth client ID with client ID: {client_id}")
    print("\n3. Under 'Authorized redirect URIs', make sure the following URIs are added:")
    for uri in redirect_uris:
        print(f"   - {uri}")
    print("\n4. Under 'Authorized JavaScript origins', make sure the following origins are added:")
    print(f"   - https://mobilize-crm.org")
    print(f"   - https://mobilize-crm-1069318103780.us-central1.run.app")
    print("\n5. Click 'Save' to update the configuration")
    
    # Check if the domains are accessible
    print("\nChecking domain accessibility:")
    for domain in ["https://mobilize-crm.org", "https://mobilize-crm-1069318103780.us-central1.run.app"]:
        try:
            response = requests.head(f"{domain}/api/auth/login-page", timeout=5)
            print(f"  - {domain}: {'Accessible' if response.status_code < 400 else f'Error (Status: {response.status_code})'}")
        except Exception as e:
            print(f"  - {domain}: Error ({str(e)})")
    
    return True

if __name__ == "__main__":
    check_and_fix_oauth_redirect()
