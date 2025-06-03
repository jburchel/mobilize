#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_database_schema():
    """Fix database schema issues by adding missing columns and tables."""
    # Get the database connection string from environment variable
    db_connection_string = os.getenv('DB_CONNECTION_STRING')
    
    if not db_connection_string:
        print("Error: DB_CONNECTION_STRING environment variable not set")
        sys.exit(1)
    
    print(f"Connecting to database...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Fix contacts table - add address column if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'address'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding address column to contacts table...")
            cursor.execute("""
                ALTER TABLE contacts ADD COLUMN address TEXT;
            """)
            print("Successfully added address column to contacts table")
        else:
            print("address column already exists in contacts table")
        
        # Check if churches table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = 'churches'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("Creating churches table...")
            cursor.execute("""
                CREATE TABLE churches (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    email TEXT,
                    website TEXT,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                );
            """)
            print("Successfully created churches table")
        else:
            print("churches table already exists")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        print("Database connection closed")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_database_schema()
    if success:
        print("Script completed successfully")
    else:
        print("Script failed")
        sys.exit(1)
