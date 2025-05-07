#!/usr/bin/env python3
"""
Database Connection Fix Script
This script applies the verified Supabase connection parameters
from our MCP verification.
"""

import os
import sys
import shutil
from pathlib import Path

# Root directory
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
ENV_PROD_FILE = ROOT_DIR / '.env.production'
ENV_PROD_BACKUP = ROOT_DIR / '.env.production.backup'

# The verified working connection string from Supabase MCP
VERIFIED_CONNECTION_STRING = "postgresql://postgres:postgres@fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres?sslmode=require"

def backup_env_file():
    """Create a backup of the .env.production file"""
    if ENV_PROD_FILE.exists():
        print(f"Creating backup of {ENV_PROD_FILE} to {ENV_PROD_BACKUP}")
        shutil.copy2(ENV_PROD_FILE, ENV_PROD_BACKUP)
        return True
    else:
        print(f"Error: {ENV_PROD_FILE} does not exist")
        return False

def update_connection_string():
    """Update the DB_CONNECTION_STRING in .env.production with verified connection"""
    if not ENV_PROD_FILE.exists():
        print(f"Error: {ENV_PROD_FILE} does not exist")
        return False
    
    # Read the current .env.production file
    with open(ENV_PROD_FILE, 'r') as f:
        lines = f.readlines()
    
    # Find and update the DB_CONNECTION_STRING line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('DB_CONNECTION_STRING='):
            old_string = line.strip()
            print(f"Replacing: {old_string}")
            new_string = f"DB_CONNECTION_STRING={VERIFIED_CONNECTION_STRING}\n"
            lines[i] = new_string
            updated = True
            print(f"With: {new_string.strip()}")
            break
    
    if not updated:
        print("DB_CONNECTION_STRING not found in .env.production")
        # Add it to the file
        lines.append(f"DB_CONNECTION_STRING={VERIFIED_CONNECTION_STRING}\n")
        print(f"Added: DB_CONNECTION_STRING={VERIFIED_CONNECTION_STRING}")
    
    # Write the updated .env.production file
    with open(ENV_PROD_FILE, 'w') as f:
        f.writelines(lines)
    
    print(f"\nSuccessfully updated {ENV_PROD_FILE}")
    return True

def main():
    print("=== Applying Verified Database Connection String ===")
    
    # Backup .env.production file
    if not backup_env_file():
        return 1
    
    # Update DB_CONNECTION_STRING
    if not update_connection_string():
        return 1
    
    print("\n✅ Database configuration updated successfully!")
    print("The verified connection string from Supabase MCP has been applied.")
    print("\nPlease run 'FLASK_ENV=production python3 scripts/deployment/verify_migration.py' to verify the connection.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 