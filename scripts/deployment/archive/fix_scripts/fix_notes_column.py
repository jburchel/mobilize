#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_notes_column():
    """Add notes column to contacts table if it doesn't exist."""
    # Get the database connection string from environment variable
    db_connection_string = os.getenv('DB_CONNECTION_STRING')
    
    if not db_connection_string:
        print("Error: DB_CONNECTION_STRING environment variable not set")
        sys.exit(1)
    
    print("Connecting to database...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Add notes column to contacts table if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'notes'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding notes column to contacts table...")
            cursor.execute("""
                ALTER TABLE contacts ADD COLUMN notes TEXT;
            """)
            print("Successfully added notes column to contacts table")
        else:
            print("notes column already exists in contacts table")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        print("Database connection closed")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_notes_column()
    if success:
        print("Script completed successfully")
    else:
        print("Script failed")
        sys.exit(1)
