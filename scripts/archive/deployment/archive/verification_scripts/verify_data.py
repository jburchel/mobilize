#!/usr/bin/env python3
"""
Data Verification Script for Mobilize CRM
This script verifies that data has been properly migrated to PostgreSQL.
"""

import os
import sys
import psycopg2
import pandas as pd
from pathlib import Path
from tabulate import tabulate

# PostgreSQL connection parameters
PG_PARAMS = {
    'host': 'fwnitauuyzxnsvgsbrzr.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432,
    'connect_timeout': 30,
    'sslmode': 'require'
}

# List of key tables to check
KEY_TABLES = [
    'users',
    'people',
    'contacts',
    'churches',
    'offices',
    'tasks',
    'communications',
    'pipeline_stages',
    'role_permissions'
]

# Sample verification queries
VERIFICATION_QUERIES = [
    {
        'name': 'User Count',
        'query': 'SELECT COUNT(*) FROM users',
        'description': 'Total number of users'
    },
    {
        'name': 'Contact Count by Office',
        'query': '''
            SELECT o.name AS office_name, COUNT(c.id) AS contact_count
            FROM contacts c
            JOIN people p ON c.person_id = p.id
            JOIN offices o ON p.office_id = o.id
            GROUP BY o.name
            ORDER BY contact_count DESC
        ''',
        'description': 'Distribution of contacts across offices'
    },
    {
        'name': 'Tasks by Status',
        'query': '''
            SELECT status, COUNT(*) AS task_count
            FROM tasks
            GROUP BY status
            ORDER BY task_count DESC
        ''',
        'description': 'Distribution of tasks by status'
    },
    {
        'name': 'Communications by Type',
        'query': '''
            SELECT type, COUNT(*) AS comm_count
            FROM communications
            GROUP BY type
            ORDER BY comm_count DESC
        ''',
        'description': 'Distribution of communications by type'
    },
    {
        'name': 'Pipeline Stages',
        'query': '''
            SELECT name, position, pipeline_id
            FROM pipeline_stages
            ORDER BY pipeline_id, position
        ''',
        'description': 'Pipeline stages in order'
    },
    {
        'name': 'Orphaned Records Check',
        'query': '''
            SELECT 
                (SELECT COUNT(*) FROM people p WHERE p.office_id IS NOT NULL AND 
                 NOT EXISTS (SELECT 1 FROM offices o WHERE o.id = p.office_id)) AS orphaned_people,
                (SELECT COUNT(*) FROM contacts c WHERE c.person_id IS NOT NULL AND 
                 NOT EXISTS (SELECT 1 FROM people p WHERE p.id = c.person_id)) AS orphaned_contacts,
                (SELECT COUNT(*) FROM tasks t WHERE t.assignee_id IS NOT NULL AND 
                 NOT EXISTS (SELECT 1 FROM users u WHERE u.id = t.assignee_id)) AS orphaned_tasks,
                (SELECT COUNT(*) FROM communications c WHERE c.contact_id IS NOT NULL AND 
                 NOT EXISTS (SELECT 1 FROM contacts co WHERE co.id = c.contact_id)) AS orphaned_communications
        ''',
        'description': 'Check for orphaned records with invalid foreign keys'
    }
]

def connect_database():
    """Connect to the PostgreSQL database."""
    try:
        print("Connecting to PostgreSQL database...")
        print(f"Host: {PG_PARAMS['host']}, Database: {PG_PARAMS['database']}, User: {PG_PARAMS['user']}")
        conn = psycopg2.connect(**PG_PARAMS)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def check_table_data(conn):
    """Check basic statistics for key tables."""
    print("\n== Table Statistics ==")
    cursor = conn.cursor()
    
    results = []
    
    for table in KEY_TABLES:
        try:
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            # Get primary key column
            cursor.execute(f"""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = '{table}'::regclass
                AND i.indisprimary
            """)
            pk_column = cursor.fetchone()
            pk_column = pk_column[0] if pk_column else 'id'
            
            # Get max ID
            cursor.execute(f"SELECT MAX({pk_column}) FROM {table}")
            max_id = cursor.fetchone()[0]
            
            # Get sequence info if it exists
            sequence_name = f"{table}_{pk_column}_seq"
            try:
                cursor.execute(f"SELECT last_value FROM {sequence_name}")
                seq_value = cursor.fetchone()[0]
                sequence_status = f"Last value: {seq_value}"
            except:
                sequence_status = "No sequence found"
            
            results.append({
                'Table': table,
                'Rows': count,
                'Max ID': max_id or 0,
                'Sequence': sequence_status
            })
            
        except Exception as e:
            print(f"Error checking table {table}: {e}")
    
    print(tabulate(results, headers="keys", tablefmt="grid"))
    return True

def run_verification_queries(conn):
    """Run a set of verification queries to check data integrity."""
    print("\n== Data Verification Queries ==")
    
    passed = True
    
    for query_info in VERIFICATION_QUERIES:
        print(f"\n--- {query_info['name']} ---")
        print(f"Description: {query_info['description']}")
        
        try:
            # Run the query and convert to DataFrame for nice display
            df = pd.read_sql_query(query_info['query'], conn)
            
            if len(df) > 0:
                print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))
                
                # Special check for orphaned records
                if query_info['name'] == 'Orphaned Records Check':
                    has_orphans = False
                    for col in df.columns:
                        if df[col].iloc[0] > 0:
                            print(f"❌ Found {df[col].iloc[0]} orphaned records in {col}")
                            has_orphans = True
                            passed = False
                    
                    if not has_orphans:
                        print("✅ No orphaned records found")
            else:
                print("No results returned")
                
            print(f"✅ Query completed successfully")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            passed = False
    
    return passed

def verify_sequences(conn):
    """Verify that sequences are properly set up."""
    print("\n== Sequence Verification ==")
    cursor = conn.cursor()
    
    sequences_ok = True
    
    for table in KEY_TABLES:
        try:
            # Get primary key column
            cursor.execute(f"""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = '{table}'::regclass
                AND i.indisprimary
            """)
            pk_column = cursor.fetchone()
            if not pk_column:
                print(f"⚠️ Could not determine primary key for {table}, skipping")
                continue
                
            pk_column = pk_column[0]
            sequence_name = f"{table}_{pk_column}_seq"
            
            # Get max ID
            cursor.execute(f"SELECT MAX({pk_column}) FROM {table}")
            max_id = cursor.fetchone()[0]
            
            if max_id is None:
                print(f"Table {table} is empty, skipping sequence check")
                continue
            
            # Get current sequence value
            try:
                cursor.execute(f"SELECT last_value FROM {sequence_name}")
                seq_value = cursor.fetchone()[0]
                
                if seq_value >= max_id:
                    print(f"✅ {table} sequence is correctly set: {seq_value} >= {max_id}")
                else:
                    print(f"❌ {table} sequence is incorrectly set: {seq_value} < {max_id}")
                    
                    # Fix the sequence
                    cursor.execute(f"SELECT setval('{sequence_name}', {max_id}, true)")
                    print(f"   Sequence fixed. New value: {max_id+1}")
                    conn.commit()
                    
                    sequences_ok = False
            except Exception as e:
                print(f"⚠️ Could not check sequence for {table}: {e}")
        
        except Exception as e:
            print(f"Error checking sequence for {table}: {e}")
    
    return sequences_ok

def main():
    print("=== Data Migration Verification ===")
    
    # Connect to the database
    conn = connect_database()
    
    try:
        # Check table data
        table_check = check_table_data(conn)
        
        # Verify sequences
        sequence_check = verify_sequences(conn)
        
        # Run verification queries
        query_check = run_verification_queries(conn)
        
        # Summarize results
        print("\n=== Verification Summary ===")
        print(f"Table Statistics: {'✅ Pass' if table_check else '❌ Fail'}")
        print(f"Sequence Verification: {'✅ Pass' if sequence_check else '❌ Fail'}")
        print(f"Data Integrity Checks: {'✅ Pass' if query_check else '❌ Fail'}")
        
        if table_check and sequence_check and query_check:
            print("\n✅ All data migration verification checks passed!")
            print("The data appears to have been properly migrated to PostgreSQL.")
            return 0
        else:
            print("\n⚠️ Some verification checks failed.")
            print("Please review the logs and fix any issues before proceeding.")
            return 1
            
    except Exception as e:
        print(f"Error during verification: {e}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main()) 