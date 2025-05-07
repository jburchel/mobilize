#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_user_id_column():
    """Add user_id column to contacts table if it doesn't exist."""
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
        
        # Add user_id column to contacts table if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'user_id'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding user_id column to contacts table...")
            cursor.execute("""
                ALTER TABLE contacts ADD COLUMN user_id INTEGER;
            """)
            print("Successfully added user_id column to contacts table")
            
            # Get the first admin user ID to set as default
            cursor.execute("""
                SELECT id FROM users WHERE role = 'super_admin' OR role = 'office_admin' LIMIT 1;
            """)
            result = cursor.fetchone()
            default_user_id = result[0] if result else 1
            
            # Set a default value for existing records
            print(f"Setting default user_id={default_user_id} for existing records...")
            cursor.execute(f"""
                UPDATE contacts SET user_id = {default_user_id} WHERE user_id IS NULL;
            """)
            print("Successfully updated existing records with default user_id")
        else:
            print("user_id column already exists in contacts table")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        print("Database connection closed")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_user_id_column()
    if success:
        print("Script completed successfully")
    else:
        print("Script failed")
        sys.exit(1)
