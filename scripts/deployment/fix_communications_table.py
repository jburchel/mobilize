#!/usr/bin/env python3

"""
Migration script to add the 'sender' column to the communications table in PostgreSQL.

This script addresses the error: Mapper 'Mapper[Communication(communications)]' has no property 'sender'

Usage:
    export DB_CONNECTION_STRING="your_postgresql_connection_string"
    python3 fix_communications_table.py
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection string from environment variable
db_connection_string = os.environ.get('DB_CONNECTION_STRING')
if not db_connection_string:
    print("Error: DB_CONNECTION_STRING environment variable not set.")
    sys.exit(1)

print(f"Using database connection: {db_connection_string}")

try:
    # Connect to PostgreSQL database
    conn = psycopg2.connect(db_connection_string)
    conn.autocommit = False  # Start a transaction
    cursor = conn.cursor()
    print("Connected to PostgreSQL database")
    
    # Check if the 'sender' column already exists
    cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'communications' AND column_name = 'sender';
    """)
    
    if cursor.fetchone() is None:
        # Add 'sender' column to communications table
        print("Adding 'sender' column to communications table...")
        cursor.execute("""
        ALTER TABLE communications 
        ADD COLUMN sender VARCHAR(255);
        """)
        print("'sender' column added successfully")
    else:
        print("'sender' column already exists in communications table")
    
    # Commit the transaction
    conn.commit()
    print("All changes committed successfully")
    
    # Close the connection
    cursor.close()
    conn.close()
    
    print("Migration completed successfully")
    
except Exception as e:
    print(f"Error: {e}")
    # Rollback the transaction in case of error
    if 'conn' in locals() and conn:
        conn.rollback()
        print("Transaction rolled back due to error")
    sys.exit(1)
