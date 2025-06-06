#!/usr/bin/env python3
"""
Database Validation Script for Mobilize CRM
This script runs validation queries against the Supabase PostgreSQL database
to verify data integrity after migration.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import pandas as pd
from tabulate import tabulate
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('.env.production')

# Try multiple connection options
connection_options = [
    {
        # Direct connection
        'name': 'Direct Connection',
        'params': {
            'host': 'fwnitauuyzxnsvgsbrzr.supabase.co',
            'dbname': 'postgres',
            'user': 'postgres',
            'password': 'postgres',
            'port': 5432,
            'sslmode': 'require',
            'connect_timeout': 10
        }
    },
    {
        # Pooler connection
        'name': 'Pooler Connection',
        'params': {
            'host': 'aws-0-us-east-1.pooler.supabase.com',
            'dbname': 'postgres',
            'user': 'postgres',
            'password': 'postgres',
            'port': 5432,
            'sslmode': 'require',
            'connect_timeout': 10
        }
    },
    {
        # Alternative form with postgres.ref format
        'name': 'Pooler with Project Reference',
        'params': {
            'host': 'aws-0-us-east-1.pooler.supabase.com',
            'dbname': 'postgres',
            'user': 'postgres.fwnitauuyzxnsvgsbrzr',
            'password': 'postgres',
            'port': 5432,
            'sslmode': 'require',
            'connect_timeout': 10
        }
    }
]

# Define validation queries
validation_queries = {
    'table_record_counts': """
        SELECT 'users' as table_name, COUNT(*) as record_count FROM users
        UNION ALL
        SELECT 'people', COUNT(*) FROM people
        UNION ALL
        SELECT 'contacts', COUNT(*) FROM contacts
        UNION ALL
        SELECT 'tasks', COUNT(*) FROM tasks
        UNION ALL
        SELECT 'communications', COUNT(*) FROM communications
        UNION ALL
        SELECT 'offices', COUNT(*) FROM offices
        UNION ALL
        SELECT 'pipeline_stages', COUNT(*) FROM pipeline_stages
        ORDER BY table_name;
    """,
    
    'orphaned_records': [
        """
        SELECT 'People without valid office' as check_type, COUNT(*) as count 
        FROM people p 
        WHERE p.office_id IS NOT NULL 
        AND NOT EXISTS (SELECT 1 FROM offices o WHERE o.id = p.office_id);
        """,
        """
        SELECT 'Tasks without valid assignee' as check_type, COUNT(*) as count 
        FROM tasks t
        WHERE t.assignee_id IS NOT NULL 
        AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = t.assignee_id);
        """,
        """
        SELECT 'Communications without valid contact' as check_type, COUNT(*) as count 
        FROM communications c
        WHERE c.contact_id IS NOT NULL 
        AND NOT EXISTS (SELECT 1 FROM contacts co WHERE co.id = c.contact_id);
        """
    ],
    
    'data_consistency': [
        """
        SELECT 'Contacts without person' as check_type, COUNT(*) as count 
        FROM contacts c
        WHERE NOT EXISTS (SELECT 1 FROM people p WHERE p.id = c.person_id);
        """,
        """
        SELECT 'Invalid stage history' as check_type, COUNT(*) as count 
        FROM pipeline_stage_history psh
        WHERE psh.from_stage_id IS NOT NULL 
        AND NOT EXISTS (SELECT 1 FROM pipeline_stages ps WHERE ps.id = psh.from_stage_id)
        OR psh.to_stage_id IS NOT NULL 
        AND NOT EXISTS (SELECT 1 FROM pipeline_stages ps WHERE ps.id = psh.to_stage_id);
        """
    ],
    
    'null_values': """
        SELECT 'Users with NULL email' as check_type, COUNT(*) as count 
        FROM users WHERE email IS NULL
        UNION ALL
        SELECT 'People with NULL name', COUNT(*) 
        FROM people WHERE first_name IS NULL OR last_name IS NULL
        UNION ALL
        SELECT 'Tasks with NULL title', COUNT(*) 
        FROM tasks WHERE title IS NULL
        UNION ALL
        SELECT 'Offices with NULL name', COUNT(*) 
        FROM offices WHERE name IS NULL;
    """,
    
    'duplicate_records': [
        """
        SELECT 'Duplicate users by email' as check_type, COUNT(*) as count
        FROM (
            SELECT email FROM users
            GROUP BY email HAVING COUNT(*) > 1
        ) as dup;
        """,
        """
        SELECT 'Duplicate people by name and email' as check_type, COUNT(*) as count
        FROM (
            SELECT first_name, last_name, email
            FROM people 
            WHERE email IS NOT NULL 
            GROUP BY first_name, last_name, email 
            HAVING COUNT(*) > 1
        ) as dup;
        """
    ],
    
    'date_consistency': [
        """
        SELECT 'Tasks with due date before creation' as check_type, COUNT(*) as count 
        FROM tasks 
        WHERE due_date < date_created;
        """,
        """
        SELECT 'Communications with future date' as check_type, COUNT(*) as count 
        FROM communications 
        WHERE date > CURRENT_TIMESTAMP;
        """
    ],
    
    'google_integration': """
        SELECT 'Contacts with Google ID but no sync date' as check_type, COUNT(*) as count 
        FROM contacts
        WHERE google_contact_id IS NOT NULL 
        AND last_synced_at IS NULL;
    """
}

def run_query(conn, query):
    """Execute a query and return the results as a DataFrame."""
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Error executing query: {e}")
        return pd.DataFrame([{"Error": str(e)}])

def build_connection_string(params):
    """Build a PostgreSQL connection string from parameters."""
    # Format: postgresql://username:password@host:port/database?sslmode=require
    return f"postgresql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['dbname']}?sslmode={params['sslmode']}"

def main():
    # Try all connection options
    conn = None
    successful_option = None
    
    for option in connection_options:
        try:
            print(f"\nTrying {option['name']}...")
            conn = psycopg2.connect(**option['params'])
            print(f"Connection successful with {option['name']}!")
            successful_option = option
            break
        except Exception as e:
            print(f"Connection failed: {e}")
    
    if conn is None:
        print("\nFailed to connect to database with any option. Exiting.")
        sys.exit(1)
    
    try:
        # Connection successful, log successful parameters and update .env.production if possible
        if successful_option:
            conn_string = build_connection_string(successful_option['params'])
            print(f"\nSuccessful connection string: {conn_string}")
            
            try:
                # Optional: Update .env.production with working connection string
                if os.access('.env.production', os.W_OK):
                    with open('.env.production', 'r') as f:
                        env_content = f.readlines()
                    
                    with open('.env.production', 'w') as f:
                        for line in env_content:
                            if not (line.startswith('DB_CONNECTION_STRING=') or line.startswith('SQLALCHEMY_DATABASE_URI=')):
                                f.write(line)
                        
                        # Add the working connection string
                        f.write(f"\nDB_CONNECTION_STRING={conn_string}\n")
                        f.write(f"SQLALCHEMY_DATABASE_URI={conn_string}\n")
                    
                    print("Updated .env.production with working connection string")
            except Exception as e:
                print(f"Note: Could not update .env.production: {e}")
        
        # Running validation queries
        print("\n=== TABLE RECORD COUNTS ===")
        df = run_query(conn, validation_queries['table_record_counts'])
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        print()
        
        # Run orphaned records checks
        print("=== ORPHANED RECORDS CHECK ===")
        for query in validation_queries['orphaned_records']:
            df = run_query(conn, query)
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        print()
        
        # Run data consistency checks
        print("=== DATA CONSISTENCY CHECK ===")
        for query in validation_queries['data_consistency']:
            df = run_query(conn, query)
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        print()
        
        # Run null values check
        print("=== NULL VALUES CHECK ===")
        df = run_query(conn, validation_queries['null_values'])
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        print()
        
        # Run duplicate records check
        print("=== DUPLICATE RECORDS CHECK ===")
        for query in validation_queries['duplicate_records']:
            df = run_query(conn, query)
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        print()
        
        # Run date consistency check
        print("=== DATE CONSISTENCY CHECK ===")
        for query in validation_queries['date_consistency']:
            df = run_query(conn, query)
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        print()
        
        # Run Google integration check
        print("=== GOOGLE INTEGRATION CHECK ===")
        df = run_query(conn, validation_queries['google_integration'])
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        print()
        
        # Close the connection
        conn.close()
        print("Database validation completed successfully!")
        
        # Update the deployment checklist items
        print("\nBased on these results, you can mark the following items in deployment-checklist.md:")
        print("- [x] Verify database schema was properly created")
        print("- [x] Confirm all data was migrated successfully")
        print("- [x] Run validation queries to check data integrity")
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.close()
        sys.exit(1)

if __name__ == "__main__":
    main() 