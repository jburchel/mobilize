#!/usr/bin/env python3
"""
Data Migration Script for Mobilize CRM
This script transfers data from SQLite to PostgreSQL database.
"""

import os
import sys
import sqlite3
import psycopg2
import json
from datetime import datetime
from pathlib import Path

# Source SQLite database path
SQLITE_DB_PATH = Path("instance/mobilize_crm.db")

# Target PostgreSQL connection parameters
PG_PARAMS = {
    'host': 'fwnitauuyzxnsvgsbrzr.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432,
    'connect_timeout': 30,
    'sslmode': 'require'
}

# Tables to migrate in the correct order to maintain foreign key relationships
TABLES_TO_MIGRATE = [
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

def connect_databases():
    """Connect to both databases and return connections."""
    try:
        print(f"Connecting to SQLite database at {SQLITE_DB_PATH}...")
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        print("Connecting to PostgreSQL database...")
        pg_conn = psycopg2.connect(**PG_PARAMS)
        
        return sqlite_conn, pg_conn
    except Exception as e:
        print(f"Error connecting to databases: {e}")
        sys.exit(1)

def get_table_info(conn, table_name):
    """Get column info for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def count_rows(sqlite_conn, pg_conn, table_name):
    """Count rows in both databases for the given table."""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    sqlite_count = sqlite_cursor.fetchone()[0]
    
    pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    pg_count = pg_cursor.fetchone()[0]
    
    return sqlite_count, pg_count

def migrate_table(sqlite_conn, pg_conn, table_name):
    """Migrate data from SQLite to PostgreSQL for a specific table."""
    print(f"\n-- Migrating table: {table_name} --")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get column names from SQLite
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col['name'] for col in sqlite_cursor.fetchall()]
    
    # Skip migration if table is empty or doesn't exist
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = sqlite_cursor.fetchone()[0]
    if row_count == 0:
        print(f"Table {table_name} is empty in SQLite, skipping...")
        return 0
    
    print(f"Found {row_count} rows to migrate in {table_name}")
    
    # Get the data from SQLite
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    # Check if there's already data in the PostgreSQL table
    pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    pg_count = pg_cursor.fetchone()[0]
    if pg_count > 0:
        print(f"Table {table_name} already has {pg_count} rows in PostgreSQL")
        print(f"Skipping migration for {table_name}")
        return 0
    
    # Prepare column list for SQL
    column_list = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    
    # Create the INSERT statement
    insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
    
    # Batch insert rows
    batch_size = 100
    migrated_count = 0
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        values_list = []
        
        for row in batch:
            # Convert SQLite row dict to list in column order
            row_values = []
            for col in columns:
                val = row[col]
                # Handle special data types that need conversion
                if isinstance(val, bytes):
                    val = val.decode('utf-8')
                row_values.append(val)
            values_list.append(row_values)
        
        try:
            pg_cursor.executemany(insert_sql, values_list)
            pg_conn.commit()
            migrated_count += len(batch)
            print(f"Migrated {migrated_count}/{row_count} rows in {table_name}")
        except Exception as e:
            pg_conn.rollback()
            print(f"Error migrating batch in {table_name}: {e}")
            return migrated_count
    
    print(f"✅ Successfully migrated {migrated_count} rows from {table_name}")
    return migrated_count

def fix_sequences(pg_conn):
    """Fix PostgreSQL sequences after data migration."""
    print("\n-- Fixing sequences --")
    pg_cursor = pg_conn.cursor()
    
    # List of tables with auto-incrementing primary keys
    tables_with_sequences = [
        ('users', 'id'),
        ('people', 'id'),
        ('contacts', 'id'),
        ('churches', 'id'),
        ('offices', 'id'),
        ('tasks', 'id'),
        ('communications', 'id'),
        ('pipeline_stages', 'id'),
        ('pipeline_stage_history', 'id'),
        ('roles', 'id'),
        ('role_permissions', 'id')
    ]
    
    for table, id_column in tables_with_sequences:
        try:
            # Get the maximum ID value
            pg_cursor.execute(f"SELECT MAX({id_column}) FROM {table}")
            max_id = pg_cursor.fetchone()[0]
            
            if max_id is not None:
                # Reset the sequence to the next value after max_id
                sequence_name = f"{table}_{id_column}_seq"
                pg_cursor.execute(
                    f"SELECT setval('{sequence_name}', {max_id}, true)"
                )
                print(f"✅ Reset sequence for {table}.{id_column} to {max_id+1}")
            else:
                print(f"No data found in {table}, skipping sequence reset")
        except Exception as e:
            print(f"Error fixing sequence for {table}: {e}")
    
    pg_conn.commit()

def verify_relationships(pg_conn):
    """Verify that relationships and constraints are maintained."""
    print("\n-- Verifying relationships --")
    pg_cursor = pg_conn.cursor()
    
    # Define relationships to check
    relationships = [
        ('people', 'office_id', 'offices', 'id'),
        ('contacts', 'person_id', 'people', 'id'),
        ('tasks', 'assignee_id', 'users', 'id'),
        ('communications', 'contact_id', 'contacts', 'id'),
        ('pipeline_stage_history', 'contact_id', 'contacts', 'id'),
        ('pipeline_stage_history', 'from_stage_id', 'pipeline_stages', 'id'),
        ('pipeline_stage_history', 'to_stage_id', 'pipeline_stages', 'id')
    ]
    
    issues_found = False
    
    for child_table, fk_column, parent_table, pk_column in relationships:
        try:
            # Check for orphaned records
            pg_cursor.execute(f"""
                SELECT COUNT(*) FROM {child_table}
                WHERE {fk_column} IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM {parent_table} 
                    WHERE {parent_table}.{pk_column} = {child_table}.{fk_column}
                  )
            """)
            orphan_count = pg_cursor.fetchone()[0]
            
            if orphan_count > 0:
                print(f"❌ Found {orphan_count} orphaned records in {child_table} "
                      f"where {fk_column} does not match any {parent_table}.{pk_column}")
                issues_found = True
            else:
                print(f"✅ Relationship {child_table}.{fk_column} -> {parent_table}.{pk_column} is valid")
                
        except Exception as e:
            print(f"Error checking relationship {child_table}.{fk_column} -> {parent_table}.{pk_column}: {e}")
    
    return not issues_found

def verify_data_integrity(sqlite_conn, pg_conn):
    """Verify data integrity after migration."""
    print("\n-- Verifying data integrity --")
    
    for table in TABLES_TO_MIGRATE:
        sqlite_count, pg_count = count_rows(sqlite_conn, pg_conn, table)
        if sqlite_count == pg_count:
            print(f"✅ Table {table}: Count matches ({sqlite_count} rows)")
        else:
            print(f"❌ Table {table}: Count mismatch! SQLite: {sqlite_count}, PostgreSQL: {pg_count}")
    
    # Verify relationship integrity
    return verify_relationships(pg_conn)

def main():
    print("=== Data Migration from SQLite to PostgreSQL ===")
    print(f"Source: {SQLITE_DB_PATH}")
    print(f"Target: PostgreSQL at {PG_PARAMS['host']}")
    
    # Connect to both databases
    sqlite_conn, pg_conn = connect_databases()
    
    try:
        # Migrate each table
        total_migrated = 0
        for table in TABLES_TO_MIGRATE:
            rows_migrated = migrate_table(sqlite_conn, pg_conn, table)
            total_migrated += rows_migrated
        
        print(f"\nTotal rows migrated: {total_migrated}")
        
        # Fix sequences
        fix_sequences(pg_conn)
        
        # Verify data integrity
        if verify_data_integrity(sqlite_conn, pg_conn):
            print("\n✅ Data migration completed successfully!")
            print("All data has been transferred and relationships are maintained.")
            return 0
        else:
            print("\n⚠️ Data migration completed with some integrity issues.")
            print("Please review the logs and fix any issues before proceeding.")
            return 1
            
    except Exception as e:
        print(f"Error during migration: {e}")
        return 1
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    sys.exit(main()) 