#!/usr/bin/env python3
"""
Comprehensive Database Migration Verification Script
This script checks that the PostgreSQL database has been properly set up
with all the required tables, relationships, and migration tracking.
"""

import os
import sys
import psycopg2
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()

# Determine the environment
ENV = os.getenv('FLASK_ENV', 'development')

# Load the appropriate .env file
env_file = ROOT_DIR / f'.env.{ENV}'
if env_file.exists():
    print(f"Loading environment from {env_file}")
    load_dotenv(env_file)
else:
    # Try the regular .env file
    env_file = ROOT_DIR / '.env'
    if env_file.exists():
        print(f"Loading environment from {env_file}")
        load_dotenv(env_file)
    else:
        print("No .env file found")

# Get connection parameters from environment
DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING')

# Parse the connection string if it exists
if DB_CONNECTION_STRING and DB_CONNECTION_STRING.startswith('postgresql://'):
    print(f"Using DB_CONNECTION_STRING: {DB_CONNECTION_STRING}")
    # Connection will be made directly with the connection string
else:
    print("No valid DB_CONNECTION_STRING found in environment variables")
    # Fallback to hardcoded parameters
    print("Falling back to default connection parameters")

# List of expected tables based on our models
EXPECTED_TABLES = [
    'users', 'people', 'contacts', 'churches', 'offices', 
    'tasks', 'communications', 'pipeline_stages', 'pipeline_stage_history',
    'roles', 'role_permissions', 'alembic_version'
]

def check_database_connection():
    """Check if we can connect to the database."""
    try:
        print("Checking database connection...")
        if DB_CONNECTION_STRING and DB_CONNECTION_STRING.startswith('postgresql://'):
            conn = psycopg2.connect(DB_CONNECTION_STRING)
        else:
            # Fallback to hardcoded parameters
            conn = psycopg2.connect(
                host='fwnitauuyzxnsvgsbrzr.supabase.co',
                database='postgres',
                user='postgres',
                password='postgres',  # Using the value we verified works
                port=5432,
                connect_timeout=30,
                sslmode='require'
            )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        print("✅ Successfully connected to the database")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")
        return False

def get_db_connection():
    """Get a database connection using the appropriate connection method."""
    if DB_CONNECTION_STRING and DB_CONNECTION_STRING.startswith('postgresql://'):
        return psycopg2.connect(DB_CONNECTION_STRING)
    else:
        # Fallback to hardcoded parameters
        return psycopg2.connect(
            host='fwnitauuyzxnsvgsbrzr.supabase.co',
            database='postgres',
            user='postgres',
            password='postgres',
            port=5432,
            connect_timeout=30,
            sslmode='require'
        )

def check_tables():
    """Check if all expected tables exist in the database."""
    try:
        print("\nChecking tables...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all tables in the public schema
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables in the database.")
        
        # Check for missing tables
        missing_tables = [table for table in EXPECTED_TABLES if table not in tables]
        
        if missing_tables:
            print("❌ Some expected tables are missing:")
            for table in missing_tables:
                print(f"  - {table}")
            return False
        else:
            print("✅ All expected tables exist in the database")
            return True
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def check_alembic_version():
    """Check if alembic_version table exists and has a version."""
    try:
        print("\nChecking alembic_version table...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if alembic_version table exists
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');")
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ alembic_version table does not exist!")
            return False
        
        # Check if there's a version in the table
        cursor.execute("SELECT version_num FROM alembic_version;")
        version = cursor.fetchone()
        
        if not version:
            print("❌ No version found in alembic_version table")
            return False
        
        print(f"✅ alembic_version table exists with version: {version[0]}")
        
        # Check if the version matches any of our migration files
        migrations_dir = Path("migrations/versions")
        if migrations_dir.exists():
            migration_files = list(migrations_dir.glob("*.py"))
            migration_ids = [file.name.split('_')[0] for file in migration_files 
                           if not file.name.startswith('__')]
            
            if version[0] in migration_ids:
                print(f"✅ Version {version[0]} matches a migration file")
            else:
                print(f"⚠️ Version {version[0]} does not match any migration files")
        
        return True
    except Exception as e:
        print(f"❌ Error checking alembic_version table: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def check_table_columns(table_name, expected_columns):
    """Check if a table has the expected columns."""
    try:
        print(f"\nChecking columns for table '{table_name}'...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get columns for the table
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}';
        """)
        
        columns = [col[0] for col in cursor.fetchall()]
        
        print(f"Found {len(columns)} columns in table '{table_name}'")
        
        # Check for missing columns
        missing_columns = [col for col in expected_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Some expected columns are missing from table '{table_name}':")
            for col in missing_columns:
                print(f"  - {col}")
            return False
        else:
            print(f"✅ All expected columns exist in table '{table_name}'")
            return True
    except Exception as e:
        print(f"❌ Error checking columns for table '{table_name}': {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    print("=== Comprehensive Database Migration Verification ===")
    
    # Check database connection
    if not check_database_connection():
        return 1
    
    # Check tables
    if not check_tables():
        return 1
    
    # Check alembic_version
    if not check_alembic_version():
        return 1
    
    # Check key tables' columns
    user_columns = ['id', 'email', 'password_hash', 'first_name', 'last_name', 'active']
    if not check_table_columns('users', user_columns):
        return 1
    
    # Check a more complex table
    task_columns = ['id', 'title', 'description', 'status', 'due_date', 'date_created', 'date_updated', 'assignee_id']
    if not check_table_columns('tasks', task_columns):
        return 1
    
    print("\n✅ All migration verification checks passed!")
    print("The database appears to be properly set up with all required tables and migration tracking.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 