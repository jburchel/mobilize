#!/usr/bin/env python3
"""
SQLite Data Extraction Script
This script extracts data from SQLite database and generates SQL INSERT statements
that can be executed directly in Supabase MCP.
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Source SQLite database path
SQLITE_DB_PATH = Path("instance/mobilize_crm.db")

# Tables to extract in the correct order to maintain foreign key relationships
TABLES_TO_EXTRACT = [
    'roles',
    'users',
    'churches',
    'offices',
    'people',
    'contacts',
    'tasks',
    'communications',
    'pipeline_stages',
    'pipeline_stage_history',
    'role_permissions'
]

def connect_sqlite():
    """Connect to SQLite database."""
    try:
        print(f"Connecting to SQLite database at {SQLITE_DB_PATH}...")
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except Exception as e:
        print(f"Error connecting to SQLite database: {e}")
        sys.exit(1)

def value_to_sql(val):
    """Convert a Python value to a SQL-safe string."""
    if val is None:
        return "NULL"
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    elif isinstance(val, datetime):
        return f"'{val.isoformat()}'"
    elif isinstance(val, (bytes, bytearray)):
        return f"'{val.decode('utf-8', errors='replace')}'"
    else:
        # Escape single quotes in strings
        val_str = str(val).replace("'", "''")
        return f"'{val_str}'"

def extract_table_data(conn, table_name, output_file):
    """Extract data from SQLite table and generate SQL INSERT statements."""
    cursor = conn.cursor()
    
    try:
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col['name'] for col in cursor.fetchall()]
        
        # Get data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"Table {table_name} is empty, skipping...")
            return 0
        
        row_count = len(rows)
        print(f"Extracting {row_count} rows from {table_name}...")
        
        # Generate SQL INSERT statements
        output_file.write(f"\n-- Data for table {table_name} ({row_count} rows)\n")
        
        for i, row in enumerate(rows):
            values = []
            for col in columns:
                values.append(value_to_sql(row[col]))
            
            columns_str = ", ".join(columns)
            values_str = ", ".join(values)
            
            output_file.write(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});\n")
            
            # Print progress every 100 rows
            if (i + 1) % 100 == 0 or i + 1 == row_count:
                print(f"  Processed {i + 1}/{row_count} rows")
        
        # Reset sequence if exists (assuming id column)
        if 'id' in columns:
            output_file.write(f"SELECT setval('{table_name}_id_seq', (SELECT MAX(id) FROM {table_name}), true);\n")
        
        return row_count
    except Exception as e:
        print(f"Error extracting data from {table_name}: {e}")
        return 0

def main():
    print("=== SQLite Data Extraction ===")
    print(f"Source: {SQLITE_DB_PATH}")
    
    if not SQLITE_DB_PATH.exists():
        print(f"Error: SQLite database file not found at {SQLITE_DB_PATH}")
        return 1
    
    # Connect to SQLite database
    sqlite_conn = connect_sqlite()
    
    # Create output file for INSERT statements
    output_path = Path("scripts/deployment/sqlite_data.sql")
    total_rows = 0
    
    try:
        with open(output_path, 'w') as output_file:
            # Write header
            output_file.write("-- SQLite data export for PostgreSQL import\n")
            output_file.write(f"-- Generated: {datetime.now().isoformat()}\n")
            output_file.write("-- Tables: " + ", ".join(TABLES_TO_EXTRACT) + "\n\n")
            
            output_file.write("BEGIN;\n")
            
            # Extract data from each table
            for table in TABLES_TO_EXTRACT:
                rows = extract_table_data(sqlite_conn, table, output_file)
                total_rows += rows
            
            output_file.write("\nCOMMIT;\n")
        
        print(f"\nTotal rows extracted: {total_rows}")
        print(f"SQL INSERT statements written to: {output_path}")
        print("\nTo import the data to PostgreSQL, you can use the Supabase MCP execute_sql tool.")
        
        return 0
    except Exception as e:
        print(f"Error during extraction: {e}")
        return 1
    finally:
        sqlite_conn.close()

if __name__ == "__main__":
    sys.exit(main()) 