#!/usr/bin/env python3
"""
Update OAuth configuration for production deployment
"""

import os
from pathlib import Path
import sys

# Get the application root directory
ROOT_DIR = Path(__file__).parent.parent.absolute()

# Production environment file
PROD_ENV_FILE = ROOT_DIR / '.env.production'

# Development environment file (for reference)
DEV_ENV_FILE = ROOT_DIR / '.env.development'

def main():
    print("Checking OAuth configuration for production deployment...")
    
    # Check if production env file exists
    if not PROD_ENV_FILE.exists():
        print(f"Error: Production environment file not found at {PROD_ENV_FILE}")
        return 1
    
    # Read current production env file
    with open(PROD_ENV_FILE, 'r') as f:
        prod_env = f.read()
    
    # Check if Google OAuth credentials are in the production env file
    if 'GOOGLE_CLIENT_ID' not in prod_env:
        print("Google OAuth credentials not found in production environment file.")
        
        # Read development env file to get the credentials
        if DEV_ENV_FILE.exists():
            with open(DEV_ENV_FILE, 'r') as f:
                dev_env = f.read()
            
            # Extract Google OAuth credentials from development env file
            import re
            client_id_match = re.search(r'GOOGLE_CLIENT_ID=([^\n]+)', dev_env)
            client_secret_match = re.search(r'GOOGLE_CLIENT_SECRET=([^\n]+)', dev_env)
            
            if client_id_match and client_secret_match:
                client_id = client_id_match.group(1)
                client_secret = client_secret_match.group(1)
                
                # Add Google OAuth credentials to production env file
                with open(PROD_ENV_FILE, 'a') as f:
                    f.write(f"\n# Google OAuth Configuration\n")
                    f.write(f"GOOGLE_CLIENT_ID={client_id}\n")
                    f.write(f"GOOGLE_CLIENT_SECRET={client_secret}\n")
                    f.write(f"BASE_URL=https://mobilize-app.onrender.com\n")
                
                print("Added Google OAuth credentials to production environment file.")
                print("\nIMPORTANT: You need to add the following redirect URI to your Google Cloud Console:")
                print("https://mobilize-app.onrender.com/api/auth/google/callback")
                print("\nFollow these steps:")
                print("1. Go to https://console.cloud.google.com/apis/credentials")
                print("2. Find and edit your OAuth 2.0 Client ID")
                print("3. Add the above URL to the 'Authorized redirect URIs' section")
                print("4. Click Save")
                print("\nAfter updating the Google Cloud Console, redeploy your application.")
            else:
                print("Error: Could not find Google OAuth credentials in development environment file.")
                return 1
        else:
            print(f"Error: Development environment file not found at {DEV_ENV_FILE}")
            return 1
    else:
        print("Google OAuth credentials already exist in production environment file.")
        print("\nMake sure the following redirect URI is added to your Google Cloud Console:")
        print("https://mobilize-app.onrender.com/api/auth/google/callback")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
