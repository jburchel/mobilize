#!/usr/bin/env python3
"""
Initialize Alembic Version Table Script
This script creates the alembic_version table and sets the current version
to match the migrations that have been applied to the database.
"""

import os
import sys
import psycopg2
from pathlib import Path

# Connection parameters
DB_PARAMS = {
    'host': 'fwnitauuyzxnsvgsbrzr.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432,
    'connect_timeout': 30,
    'sslmode': 'require'
}

def get_latest_migration_version():
    """Get the latest migration version from the migrations directory."""
    migrations_dir = Path("migrations/versions")
    if not migrations_dir.exists():
        print(f"Error: Migrations directory {migrations_dir} does not exist")
        return None
        
    # Find all migration files
    migration_files = list(migrations_dir.glob("*.py"))
    if not migration_files:
        print("Error: No migration files found")
        return None
    
    # Extract version IDs (they are in the format: 1a2b3c4d5e6f_migration_name.py)
    versions = []
    for file in migration_files:
        if file.name.startswith('__'):
            continue
        version_id = file.stem.split('_')[0]
        versions.append((version_id, file))
    
    if not versions:
        print("Error: No valid migration versions found")
        return None
    
    # Sort by filename to get the latest version
    # This assumes migrations were created in order
    versions.sort(key=lambda x: x[1].name)
    latest_version = versions[-1][0]
    
    print(f"Latest migration version: {latest_version} ({versions[-1][1].name})")
    return latest_version

def create_alembic_version_table(version):
    """Create the alembic_version table and set the version."""
    try:
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Check if alembic_version table already exists
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');")
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("alembic_version table already exists")
            
            # Check if it has a version set
            cursor.execute("SELECT version_num FROM alembic_version;")
            current_version = cursor.fetchone()
            
            if current_version:
                print(f"Current version is: {current_version[0]}")
                
                # Update the version
                choice = input(f"Do you want to update the version to {version}? (y/n): ")
                if choice.lower() == 'y':
                    cursor.execute("UPDATE alembic_version SET version_num = %s;", (version,))
                    conn.commit()
                    print(f"Updated version to: {version}")
                else:
                    print("Version not updated")
            else:
                print("No version set in alembic_version table")
                cursor.execute("INSERT INTO alembic_version (version_num) VALUES (%s);", (version,))
                conn.commit()
                print(f"Set version to: {version}")
        else:
            print("Creating alembic_version table...")
            cursor.execute("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL, 
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                );
            """)
            
            # Insert the version
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES (%s);", (version,))
            conn.commit()
            print(f"Created alembic_version table and set version to: {version}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=== Initializing Alembic Version Table ===")
    
    # Get the latest migration version
    version = get_latest_migration_version()
    if not version:
        print("Cannot proceed without a valid migration version")
        return 1
    
    # Create the alembic_version table and set the version
    if not create_alembic_version_table(version):
        return 1
    
    print("\n✅ Alembic version table initialization completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 