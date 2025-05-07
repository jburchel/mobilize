#!/usr/bin/env python3

"""
Script to update the authorized redirect URIs for the Google OAuth client.
This is necessary when deploying to a new environment like Cloud Run.
"""

import os
import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def update_oauth_redirect_uris():
    """Update the authorized redirect URIs for the Google OAuth client."""
    # Get the client ID from environment
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    if not client_id:
        print("Error: GOOGLE_CLIENT_ID environment variable not set")
        sys.exit(1)
        
    # Extract the client ID without the .apps.googleusercontent.com suffix
    client_number = client_id.split('.')[0]
    
    # Get the credentials from the FIREBASE_CREDENTIALS environment variable
    firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS')
    if not firebase_creds_json:
        print("Error: FIREBASE_CREDENTIALS environment variable not set")
        sys.exit(1)
        
    try:
        firebase_creds = json.loads(firebase_creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            firebase_creds,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
    except Exception as e:
        print(f"Error loading credentials: {str(e)}")
        sys.exit(1)
    
    # Build the Google API client
    try:
        service = build('iamcredentials', 'v1', credentials=credentials)
        
        # Get the project ID from the credentials
        project_id = firebase_creds.get('project_id')
        if not project_id:
            print("Error: Could not determine project ID from credentials")
            sys.exit(1)
            
        print(f"Using project ID: {project_id}")
        
        # Build the OAuth API client
        oauth_service = build('oauth2', 'v2', credentials=credentials)
        
        # Get the current redirect URIs
        client_info = oauth_service.userinfo().get().execute()
        print(f"Authenticated as: {client_info.get('email')}")
        
        # Now use the Cloud Resource Manager API to get the project
        crm_service = build('cloudresourcemanager', 'v1', credentials=credentials)
        project = crm_service.projects().get(projectId=project_id).execute()
        print(f"Project name: {project.get('name')}")
        
        # Now use the Cloud Run API to get the service URL
        run_service = build('run', 'v1', credentials=credentials)
        parent = f"projects/{project_id}/locations/us-central1"
        services = run_service.projects().locations().services().list(parent=parent).execute()
        
        service_urls = []
        for service in services.get('services', []):
            service_url = service.get('status', {}).get('url')
            if service_url:
                service_urls.append(service_url)
                print(f"Found service URL: {service_url}")
        
        # Add custom domain if available
        custom_domain = "https://mobilize-crm.org"
        service_urls.append(custom_domain)
        print(f"Added custom domain: {custom_domain}")
        
        # Get the OAuth client
        oauth_config_service = build('oauth2', 'v2', credentials=credentials)
        
        # Prepare the redirect URIs
        redirect_uris = []
        for url in service_urls:
            redirect_uris.append(f"{url}/api/auth/google/callback")
            
        # Add localhost for development
        redirect_uris.append("http://localhost:5000/api/auth/google/callback")
        redirect_uris.append("https://localhost:5000/api/auth/google/callback")
        
        print("\nRedirect URIs to be configured:")
        for uri in redirect_uris:
            print(f"  - {uri}")
            
        # Use the Google Cloud Console API to update the OAuth client
        # Note: This requires the OAuth API to be enabled in your project
        oauth_api_service = build('oauth2', 'v2', credentials=credentials)
        
        # Unfortunately, there's no direct API to update OAuth client redirect URIs
        # You'll need to use the Google Cloud Console UI to update them
        print("\nPlease update the redirect URIs manually in the Google Cloud Console:")
        print(f"https://console.cloud.google.com/apis/credentials/oauthclient/{client_number}?project={project_id}")
        print("\nCopy and paste the following URIs:")
        for uri in redirect_uris:
            print(uri)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
        
    print("\nScript completed. Please update the redirect URIs manually.")

if __name__ == "__main__":
    update_oauth_redirect_uris()
