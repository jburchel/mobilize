#!/usr/bin/env python3
"""
Database Connection Test Script for Mobilize CRM
This script tests the connection to the PostgreSQL database and verifies
that the alembic_version table exists.
"""

import psycopg2
import sys
from psycopg2 import sql

# Connection parameters
db_params = {
    'host': 'fwnitauuyzxnsvgsbrzr.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Fruitin2025!',
    'port': 5432
}

def main():
    try:
        # Connect to the database
        print("Connecting to Supabase PostgreSQL database...")
        conn = psycopg2.connect(**db_params)
        print("Connection successful!")
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Check if the alembic_version table exists
        print("\nChecking for alembic_version table...")
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');")
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("alembic_version table exists.")
            cursor.execute("SELECT version_num FROM alembic_version;")
            version = cursor.fetchone()
            print(f"Current version: {version[0] if version else 'No version found'}")
        else:
            print("alembic_version table does not exist! Migration tracking might be compromised.")
        
        # Check database permissions
        print("\nChecking database permissions...")
        cursor.execute("SELECT current_user;")
        current_user = cursor.fetchone()[0]
        print(f"Connected as user: {current_user}")
        
        # Check basic operations
        try:
            cursor.execute("CREATE TABLE test_table (id serial PRIMARY KEY, name VARCHAR(100));")
            print("CREATE TABLE permission: Yes")
            cursor.execute("INSERT INTO test_table (name) VALUES ('test');")
            print("INSERT permission: Yes")
            cursor.execute("SELECT * FROM test_table;")
            print("SELECT permission: Yes")
            cursor.execute("DROP TABLE test_table;")
            print("DROP TABLE permission: Yes")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Permission test failed: {e}")
        
        # List all tables in the public schema
        print("\nListing all tables in the public schema:")
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")
        
        # Close the connection
        cursor.close()
        conn.close()
        print("\nDatabase connection test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 