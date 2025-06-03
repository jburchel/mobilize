#!/usr/bin/env python3
"""
Application Configuration Update Script
This script updates the application's .env.production file with the correct
PostgreSQL connection string and other necessary settings.
"""

import os
import sys
import shutil
from pathlib import Path

# Root directory
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
ENV_PROD_FILE = ROOT_DIR / '.env.production'
ENV_PROD_BACKUP = ROOT_DIR / '.env.production.backup'

# Verified PostgreSQL connection parameters from MCP
PG_PARAMS = {
    'host': 'fwnitauuyzxnsvgsbrzr.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

# Construct the PostgreSQL connection string
PG_CONNECTION_STRING = f"postgresql://{PG_PARAMS['user']}:{PG_PARAMS['password']}@{PG_PARAMS['host']}:{PG_PARAMS['port']}/{PG_PARAMS['database']}?sslmode=require"

def backup_env_file():
    """Create a backup of the .env.production file"""
    if ENV_PROD_FILE.exists():
        print(f"Creating backup of {ENV_PROD_FILE} to {ENV_PROD_BACKUP}")
        shutil.copy2(ENV_PROD_FILE, ENV_PROD_BACKUP)
        return True
    else:
        print(f"Warning: {ENV_PROD_FILE} does not exist, will create a new one")
        return True

def update_env_file():
    """Update or create the .env.production file with the PostgreSQL connection string"""
    # Read existing .env.production if it exists
    env_vars = {}
    if ENV_PROD_FILE.exists():
        print(f"Reading existing {ENV_PROD_FILE}")
        with open(ENV_PROD_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Update or add DB_CONNECTION_STRING
    old_connection_string = env_vars.get('DB_CONNECTION_STRING', '')
    env_vars['DB_CONNECTION_STRING'] = PG_CONNECTION_STRING
    
    # Ensure FLASK_ENV is set to production
    env_vars['FLASK_ENV'] = 'production'
    
    # Ensure SQLALCHEMY_DATABASE_URI is set if it's used directly
    env_vars['SQLALCHEMY_DATABASE_URI'] = PG_CONNECTION_STRING
    
    # Write the updated .env.production file
    print(f"Writing updated {ENV_PROD_FILE}")
    with open(ENV_PROD_FILE, 'w') as f:
        f.write("# Production Environment Configuration\n")
        f.write("# Updated by scripts/deployment/update_app_config.py\n\n")
        
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ Successfully updated {ENV_PROD_FILE}")
    
    if old_connection_string and old_connection_string != PG_CONNECTION_STRING:
        print(f"\nChanged DB_CONNECTION_STRING from:")
        print(f"  {old_connection_string}")
        print(f"to:")
        print(f"  {PG_CONNECTION_STRING}")
    elif not old_connection_string:
        print(f"\nAdded DB_CONNECTION_STRING:")
        print(f"  {PG_CONNECTION_STRING}")
    else:
        print(f"\nDB_CONNECTION_STRING unchanged:")
        print(f"  {PG_CONNECTION_STRING}")
    
    return True

def main():
    print("=== Application Configuration Update ===")
    
    # Backup .env.production file
    if not backup_env_file():
        return 1
    
    # Update .env.production file
    if not update_env_file():
        return 1
    
    print("\n✅ Application configuration updated successfully!")
    print("\nTo verify the configuration:")
    print("1. Run the application with FLASK_ENV=production")
    print("2. Check logs for database connection messages")
    print("3. Verify that the application connects to PostgreSQL")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 