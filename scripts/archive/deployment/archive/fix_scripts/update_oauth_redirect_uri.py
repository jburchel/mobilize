#!/usr/bin/env python3
import requests
import sys

def update_oauth_redirect_uris():
    # Get the access token from the command line arguments
    access_token = sys.argv[1]
    
    # Google OAuth client ID
    client_id = "1069318103780-fi8f8evourdslk381p98bp69km1npq5v.apps.googleusercontent.com"
    
    # New redirect URI
    new_redirect_uri = "https://mobilize-crm.org/api/auth/google/callback"
    
    # Get the current client configuration
    url = f"https://oauth2.googleapis.com/v1/clientinfo?client_id={client_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        client_info = response.json()
        
        # Print the current redirect URIs
        print("Current redirect URIs:")
        if "redirect_uris" in client_info:
            for uri in client_info["redirect_uris"]:
                print(f"  - {uri}")
        else:
            print("  No redirect URIs found")
        
        # Check if the new redirect URI is already in the list
        if "redirect_uris" in client_info and new_redirect_uri in client_info["redirect_uris"]:
            print(f"\nThe redirect URI '{new_redirect_uri}' is already authorized.")
            return
        
        # Add the new redirect URI to the list
        if "redirect_uris" not in client_info:
            client_info["redirect_uris"] = []
        
        client_info["redirect_uris"].append(new_redirect_uri)
        
        # Update the client configuration
        update_url = f"https://oauth2.googleapis.com/v1/clientinfo?client_id={client_id}"
        update_response = requests.put(update_url, headers=headers, json=client_info)
        update_response.raise_for_status()
        
        print(f"\nSuccessfully added the redirect URI '{new_redirect_uri}'")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}")
        
        # If we got a 403 error, we need to use the Google Cloud Console UI
        if hasattr(e, "response") and e.response.status_code == 403:
            print("\nYou need to manually update the authorized redirect URIs in the Google Cloud Console:")
            print("1. Go to https://console.cloud.google.com/apis/credentials")
            print("2. Click on the OAuth 2.0 Client ID for your application")
            print("3. Add the following URI to the 'Authorized redirect URIs' list:")
            print(f"   {new_redirect_uri}")
            print("4. Click 'Save'")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_oauth_redirect_uri.py <access_token>")
        sys.exit(1)
    
    update_oauth_redirect_uris()
