#!/usr/bin/env python3
"""
Update Database Configuration Script
This script updates the database connection settings in .env.production file
to use the correct Supabase connection parameters.
"""

import os
import sys
import shutil
import psycopg2
from pathlib import Path

# Root directory
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
ENV_PROD_FILE = ROOT_DIR / '.env.production'
ENV_PROD_BACKUP = ROOT_DIR / '.env.production.backup'

# Connection string options to test
CONNECTION_STRINGS = [
    # Pooler connection
    "postgresql://postgres.fwnitauuyzxnsvgsbrzr:Fruitin2025@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require",
    # Direct connection
    "postgresql://postgres.fwnitauuyzxnsvgsbrzr:Fruitin2025@db.fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres?sslmode=require",
    # Current connection string with updated username
    "postgresql://postgres.fwnitauuyzxnsvgsbrzr:Fruitin2025!@fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres?sslmode=require",
    # Current connection string with no exclamation mark
    "postgresql://postgres.fwnitauuyzxnsvgsbrzr:Fruitin2025@fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres?sslmode=require",
]

def backup_env_file():
    """Create a backup of the .env.production file"""
    if ENV_PROD_FILE.exists():
        print(f"Creating backup of {ENV_PROD_FILE} to {ENV_PROD_BACKUP}")
        shutil.copy2(ENV_PROD_FILE, ENV_PROD_BACKUP)
        return True
    else:
        print(f"Error: {ENV_PROD_FILE} does not exist")
        return False

def test_connection_string(conn_string):
    """Test a connection string to see if it works"""
    try:
        print(f"Testing connection with: {conn_string}")
        conn = psycopg2.connect(conn_string)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            db_version = cur.fetchone()[0]
        conn.close()
        print(f"✅ Connection successful: {db_version}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def find_working_connection():
    """Test all connection strings and return the first one that works"""
    for i, conn_str in enumerate(CONNECTION_STRINGS):
        print(f"\nTesting connection string {i+1}/{len(CONNECTION_STRINGS)}:")
        if test_connection_string(conn_str):
            return conn_str
    return None

def update_connection_string():
    """Update the DB_CONNECTION_STRING in .env.production"""
    if not ENV_PROD_FILE.exists():
        print(f"Error: {ENV_PROD_FILE} does not exist")
        return False
    
    print("\nFinding a working connection string...")
    working_conn_str = find_working_connection()
    
    if not working_conn_str:
        print("❌ No working connection string found")
        return False
    
    print(f"\n✅ Found working connection string: {working_conn_str}")
    
    # Read the current .env.production file
    with open(ENV_PROD_FILE, 'r') as f:
        lines = f.readlines()
    
    # Find and update the DB_CONNECTION_STRING line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('DB_CONNECTION_STRING='):
            old_string = line.strip()
            print(f"Replacing: {old_string}")
            new_string = f"DB_CONNECTION_STRING={working_conn_str}\n"
            lines[i] = new_string
            updated = True
            print(f"With: {new_string.strip()}")
            break
    
    if not updated:
        print("DB_CONNECTION_STRING not found in .env.production")
        # Add it to the file
        lines.append(f"DB_CONNECTION_STRING={working_conn_str}\n")
        print(f"Added: DB_CONNECTION_STRING={working_conn_str}")
    
    # Write the updated .env.production file
    with open(ENV_PROD_FILE, 'w') as f:
        f.writelines(lines)
    
    print(f"\nSuccessfully updated {ENV_PROD_FILE}")
    return True

def main():
    print("=== Update Database Configuration ===")
    
    # Backup .env.production file
    if not backup_env_file():
        return 1
    
    # Update DB_CONNECTION_STRING
    if not update_connection_string():
        return 1
    
    print("\n✅ Database configuration updated successfully!")
    print("Please run 'FLASK_ENV=production python3 scripts/deployment/verify_connection.py' to verify the connection.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 