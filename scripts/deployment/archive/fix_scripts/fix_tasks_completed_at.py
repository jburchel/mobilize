#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2 import sql

# Add the parent directory to sys.path to allow importing from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Get the database connection string from environment variable or use a default
db_connection_string = os.environ.get('DB_CONNECTION_STRING', 'postgresql://postgres.fwnitauuyzxnsvgsbrzr:UK1eAogXCrBoaCyI@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require')

def add_completed_at_column():
    """Add the completed_at column to the tasks table if it doesn't exist."""
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tasks' 
            AND column_name = 'completed_at';
        """)
        
        if cursor.fetchone() is None:
            print("Adding completed_at column to tasks table...")
            # Add the completed_at column
            cursor.execute("""
                ALTER TABLE tasks 
                ADD COLUMN completed_at TIMESTAMP WITH TIME ZONE;
            """)
            print("Successfully added completed_at column to tasks table.")
        else:
            print("The completed_at column already exists in the tasks table.")
        
        # Close the connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = add_completed_at_column()
    sys.exit(0 if success else 1)
