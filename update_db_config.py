"""
Script to update database connection strings in .env.production
"""
import os
import re

def update_db_config():
    # New database configuration
    new_db_url = "postgresql://postgres.fwnitauuyzxnsvgsbrzr:Fruitin2025%21@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    new_db_conn_string = new_db_url + "?sslmode=require"
    
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