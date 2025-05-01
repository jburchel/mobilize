#!/usr/bin/env python3

"""
Fix Tasks Table Migration Script

This script adds missing columns to the tasks table in PostgreSQL.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection string from environment or use default
db_connection_string = os.getenv('DB_CONNECTION_STRING')

if not db_connection_string:
    print("Error: DB_CONNECTION_STRING environment variable not set")
    sys.exit(1)

print(f"Using database connection: {db_connection_string}")

# Connect to PostgreSQL database
try:
    conn = psycopg2.connect(db_connection_string)
    conn.autocommit = False
    cursor = conn.cursor()
    print("Connected to PostgreSQL database")
except Exception as e:
    print(f"Error connecting to PostgreSQL database: {e}")
    sys.exit(1)

# Check if the tasks table exists
cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks')")
if not cursor.fetchone()[0]:
    print("Error: 'tasks' table does not exist")
    conn.close()
    sys.exit(1)

# Check if the 'type' column exists in the tasks table
cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'tasks' AND column_name = 'type')")
type_column_exists = cursor.fetchone()[0]

try:
    if not type_column_exists:
        print("Adding 'type' column to tasks table...")
        cursor.execute("""
        ALTER TABLE tasks 
        ADD COLUMN type VARCHAR(50) DEFAULT 'general' NOT NULL
        """)
        print("'type' column added successfully")
    else:
        print("'type' column already exists")

    # Check for other required columns and add them if missing
    # Check for status column
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'tasks' AND column_name = 'status')")
    if not cursor.fetchone()[0]:
        print("Adding 'status' column to tasks table...")
        cursor.execute("""
        ALTER TABLE tasks 
        ADD COLUMN status VARCHAR(50) DEFAULT 'pending' NOT NULL
        """)
        print("'status' column added successfully")

    # Check for priority column
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'tasks' AND column_name = 'priority')")
    if not cursor.fetchone()[0]:
        print("Adding 'priority' column to tasks table...")
        cursor.execute("""
        ALTER TABLE tasks 
        ADD COLUMN priority VARCHAR(50) DEFAULT 'medium' NOT NULL
        """)
        print("'priority' column added successfully")

    # Commit the transaction
    conn.commit()
    print("All changes committed successfully")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    sys.exit(1)
finally:
    cursor.close()
    conn.close()

print("Migration completed successfully")
