#!/usr/bin/env python3
import os
import sys

def fix_google_oauth_config():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up two directories to get to the app root
    app_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Path to the google_oauth.py file
    google_oauth_path = os.path.join(app_root, 'app', 'auth', 'google_oauth.py')
    
    print(f"Fixing Google OAuth configuration in {google_oauth_path}")
    
    with open(google_oauth_path, 'r') as file:
        content = file.read()
    
    # Fix the client_config creation to ensure no extra whitespace
    if "client_id': os.getenv('GOOGLE_CLIENT_ID')" in content:
        # Replace with a version that strips whitespace
        content = content.replace(
            "client_id': os.getenv('GOOGLE_CLIENT_ID')",
            "client_id': os.getenv('GOOGLE_CLIENT_ID').strip() if os.getenv('GOOGLE_CLIENT_ID') else ''"
        )
        
        # Also fix the client_secret to be safe
        content = content.replace(
            "client_secret': os.getenv('GOOGLE_CLIENT_SECRET')",
            "client_secret': os.getenv('GOOGLE_CLIENT_SECRET').strip() if os.getenv('GOOGLE_CLIENT_SECRET') else ''"
        )
        
        print("Added .strip() to client_id and client_secret to remove any whitespace")
    
    # Write the updated content back to the file
    with open(google_oauth_path, 'w') as file:
        file.write(content)
    
    print("Google OAuth configuration fixed successfully!")
    print("Please redeploy the application for the changes to take effect.")

if __name__ == "__main__":
    fix_google_oauth_config()
