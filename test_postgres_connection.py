#!/usr/bin/env python3
"""
PostgreSQL Connection Tester for Mobilize CRM

This script tests the connection to the PostgreSQL database and verifies the schema.
"""

import os
import sys
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
load_dotenv('.env.production', override=True)

# Configuration
PG_DB_URL = os.getenv('DATABASE_URL')
if not PG_DB_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

def test_connection():
    """Test the connection to PostgreSQL"""
    print(f"Testing connection to PostgreSQL database...")
    start_time = time.time()
    
    try:
        conn = psycopg2.connect(PG_DB_URL)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        # Get connection info
        cursor.execute("SELECT current_database(), current_user")
        db_info = cursor.fetchone()
        
        print(f"Connection successful! ({time.time() - start_time:.2f}s)")
        print(f"Database: {db_info[0]}")
        print(f"User: {db_info[1]}")
        print(f"PostgreSQL version: {version}")
        
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

def check_schema(conn):
    """Check schema and list tables"""
    print("\nChecking database schema...")
    
    try:
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # List all tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        
        # Get row counts for each table
        table_stats = []
        for table in tables:
            table_name = table['table_name']
            cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
            count = cursor.fetchone()[0]
            table_stats.append((table_name, count))
        
        # Print table list with row counts
        max_name_len = max(len(name) for name, _ in table_stats)
        for name, count in table_stats:
            print(f"  {name:{max_name_len}} : {count} rows")
        
        # Check for common essential tables
        essential_tables = ['users', 'contacts', 'people', 'tasks', 'communications']
        missing_tables = [table for table in essential_tables if table not in [t[0] for t in table_stats]]
        
        if missing_tables:
            print("\nWARNING: Some essential tables are missing:")
            for table in missing_tables:
                print(f"  - {table}")
        else:
            print("\nAll essential tables are present.")
        
        cursor.close()
    except Exception as e:
        print(f"Error checking schema: {e}")

def check_constraints(conn):
    """Check foreign key constraints"""
    print("\nChecking foreign key constraints...")
    
    try:
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        cursor.execute("""
            SELECT
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name
        """)
        
        fk_constraints = cursor.fetchall()
        print(f"Found {len(fk_constraints)} foreign key constraints:")
        
        current_table = None
        for fk in fk_constraints:
            if fk['table_name'] != current_table:
                current_table = fk['table_name']
                print(f"\n  Table: {current_table}")
            
            print(f"    {fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        cursor.close()
    except Exception as e:
        print(f"Error checking constraints: {e}")

def check_indexes(conn):
    """Check indexes for performance"""
    print("\nChecking indexes...")
    
    try:
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        cursor.execute("""
            SELECT
                t.relname AS table_name,
                i.relname AS index_name,
                a.attname AS column_name
            FROM
                pg_class t,
                pg_class i,
                pg_index ix,
                pg_attribute a
            WHERE
                t.oid = ix.indrelid
                AND i.oid = ix.indexrelid
                AND a.attrelid = t.oid
                AND a.attnum = ANY(ix.indkey)
                AND t.relkind = 'r'
                AND t.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            ORDER BY
                t.relname,
                i.relname,
                a.attnum
        """)
        
        indexes = cursor.fetchall()
        print(f"Found {len(indexes)} indexed columns:")
        
        current_table = None
        current_index = None
        for idx in indexes:
            if idx['table_name'] != current_table:
                current_table = idx['table_name']
                print(f"\n  Table: {current_table}")
                current_index = None
            
            if idx['index_name'] != current_index:
                current_index = idx['index_name']
                print(f"    Index: {current_index}")
            
            print(f"      Column: {idx['column_name']}")
        
        cursor.close()
    except Exception as e:
        print(f"Error checking indexes: {e}")

def main():
    print("=== PostgreSQL Database Connection Test ===\n")
    
    # Test connection
    conn = test_connection()
    
    # Check schema
    check_schema(conn)
    
    # Check constraints
    check_constraints(conn)
    
    # Check indexes
    check_indexes(conn)
    
    # Close connection
    conn.close()
    
    print("\nDatabase connection test completed successfully!")

if __name__ == "__main__":
    main() 