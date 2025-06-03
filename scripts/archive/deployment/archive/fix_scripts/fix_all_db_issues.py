#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_all_database_issues():
    """Fix all known database schema issues."""
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
        
        # Fix 1: Add reminder_sent column to tasks table if it doesn't exist
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
        
        # Fix 2: Add address column to contacts table if it doesn't exist
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
        
        # Fix 3: Add city column to contacts table if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'city'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding city column to contacts table...")
            cursor.execute("""
                ALTER TABLE contacts ADD COLUMN city TEXT;
            """)
            print("Successfully added city column to contacts table")
        else:
            print("city column already exists in contacts table")
        
        # Fix 4: Add state column to contacts table if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'state'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding state column to contacts table...")
            cursor.execute("""
                ALTER TABLE contacts ADD COLUMN state TEXT;
            """)
            print("Successfully added state column to contacts table")
        else:
            print("state column already exists in contacts table")
        
        # Fix 5: Add zip_code column to contacts table if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'zip_code'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding zip_code column to contacts table...")
            cursor.execute("""
                ALTER TABLE contacts ADD COLUMN zip_code TEXT;
            """)
            print("Successfully added zip_code column to contacts table")
        else:
            print("zip_code column already exists in contacts table")
        
        # Fix 6: Add country column to contacts table if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'country'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding country column to contacts table...")
            cursor.execute("""
                ALTER TABLE contacts ADD COLUMN country TEXT;
            """)
            print("Successfully added country column to contacts table")
        else:
            print("country column already exists in contacts table")
        
        # Fix 7: Add notes column to contacts table if it doesn't exist
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
        
        # Fix 8: Add office_id column to contacts table if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'office_id'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding office_id column to contacts table...")
            cursor.execute("""
                ALTER TABLE contacts ADD COLUMN office_id INTEGER;
            """)
            print("Successfully added office_id column to contacts table")
            
            # Set a default value for existing records
            print("Setting default office_id=1 for existing records...")
            cursor.execute("""
                UPDATE contacts SET office_id = 1 WHERE office_id IS NULL;
            """)
            print("Successfully updated existing records with default office_id")
        else:
            print("office_id column already exists in contacts table")
        
        # Fix 9: Check if churches table exists and create it if it doesn't
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
                    id INTEGER PRIMARY KEY REFERENCES contacts(id),
                    name TEXT,
                    location TEXT,
                    main_contact_id INTEGER REFERENCES people(id),
                    senior_pastor_name TEXT,
                    denomination TEXT,
                    weekly_attendance INTEGER,
                    website TEXT,
                    owner_id INTEGER NOT NULL REFERENCES users(id),
                    virtuous BOOLEAN DEFAULT FALSE,
                    senior_pastor_phone TEXT,
                    senior_pastor_email TEXT,
                    missions_pastor_first_name TEXT,
                    missions_pastor_last_name TEXT,
                    mission_pastor_phone TEXT,
                    mission_pastor_email TEXT,
                    priority TEXT DEFAULT 'MEDIUM',
                    assigned_to TEXT DEFAULT 'UNASSIGNED',
                    source TEXT DEFAULT 'UNKNOWN',
                    referred_by TEXT,
                    info_given TEXT,
                    reason_closed TEXT,
                    year_founded INTEGER,
                    date_closed DATE
                );
            """)
            print("Successfully created churches table")
        else:
            print("churches table already exists, checking for missing columns...")
            
            # Check and add missing columns to churches table
            columns_to_check = [
                ('name', 'TEXT'),
                ('senior_pastor_name', 'TEXT'),
                ('weekly_attendance', 'INTEGER'),
                ('owner_id', 'INTEGER')
            ]
            
            for column_name, column_type in columns_to_check:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'churches' AND column_name = '{column_name}'
                    );
                """)
                column_exists = cursor.fetchone()[0]
                
                if not column_exists:
                    print(f"Adding {column_name} column to churches table...")
                    cursor.execute(f"""
                        ALTER TABLE churches ADD COLUMN {column_name} {column_type};
                    """)
                    print(f"Successfully added {column_name} column to churches table")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        print("Database connection closed")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_all_database_issues()
    if success:
        print("Script completed successfully")
    else:
        print("Script failed")
        sys.exit(1)
