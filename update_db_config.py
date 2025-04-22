"""
Script to update database connection strings in .env.production
"""
import os
import re
import urllib.parse

def update_db_config():
    # Format the database URL with proper URL encoding
    username = "postgres.fwnitauuyzxnsvgsbrzr"
    password = "IzWzdgCE78Sbf7Wg"  # This should be your current password
    hostname = "aws-0-us-east-1.pooler.supabase.com"
    port = "5432"
    database = "postgres"
    
    # URL encode the password to handle special characters
    encoded_password = urllib.parse.quote_plus(password)
    
    # Create properly formatted database URLs
    new_db_url = f"postgresql://{username}:{encoded_password}@{hostname}:{port}/{database}"
    new_db_conn_string = f"{new_db_url}?sslmode=require"
    
    print(f"New database URL: {new_db_url}")
    
    # Read existing .env.production file
    try:
        with open('.env.production', 'r') as file:
            env_content = file.read()
        
        # Update DATABASE_URL
        env_content = re.sub(
            r'DATABASE_URL=.*',
            f'DATABASE_URL={new_db_url}',
            env_content
        )
        
        # Update DB_CONNECTION_STRING
        env_content = re.sub(
            r'DB_CONNECTION_STRING=.*',
            f'DB_CONNECTION_STRING={new_db_conn_string}',
            env_content
        )
        
        # Write updated content back to file
        with open('.env.production', 'w') as file:
            file.write(env_content)
            
        print("Successfully updated database configuration in .env.production")
        
    except Exception as e:
        print(f"Error updating .env.production: {str(e)}")

if __name__ == "__main__":
    update_db_config() 