#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_tasks_reminder_sent():
    """Add reminder_sent column to tasks table if it doesn't exist."""
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
        
        # Check if the column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'tasks' AND column_name = 'reminder_sent'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding reminder_sent column to tasks table...")
            cursor.execute("""
                ALTER TABLE tasks ADD COLUMN reminder_sent BOOLEAN DEFAULT FALSE;
            """)
            print("Successfully added reminder_sent column to tasks table")
        else:
            print("reminder_sent column already exists in tasks table")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        print("Database connection closed")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_tasks_reminder_sent()
    if success:
        print("Script completed successfully")
    else:
        print("Script failed")
        sys.exit(1)
