#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for Mobilize CRM

This script migrates data from a SQLite database to a PostgreSQL database,
handling data type conversions, foreign key constraints, and providing
progress reporting throughout the process.

Usage:
    python migrate_data.py [--dry-run]

Arguments:
    --dry-run: Optional flag to preview migration without making changes
"""

import os
import sys
import time
import argparse
import sqlite3
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from datetime import datetime
from contextlib import contextmanager

# Load environment variables
load_dotenv()
load_dotenv('.env.production', override=True)

# Configuration
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'instance/mobilize.db')
PG_CONNECTION_STRING = os.getenv('DATABASE_URL')
BATCH_SIZE = 1000  # Number of records to process in each batch

# Define table migration order (respecting foreign key constraints)
TABLES_IN_ORDER = [
    'user',
    'pipelines',
    'pipeline_stages',
    'people',
    'contacts',
    'pipeline_stage_history',
    'tasks',
    'notes',
    'phone_numbers',
    'addresses',
    # Add all other tables in the correct order
]

# Column type mappings and transformations
TYPE_MAPPINGS = {
    'BOOLEAN': lambda v: 'TRUE' if v == 1 else 'FALSE' if v == 0 else 'NULL' if v is None else v,
    'TIMESTAMP': lambda v: f"'{v}'" if v else 'NULL',
    'INTEGER': lambda v: str(v) if v is not None else 'NULL',
    'TEXT': lambda v: f"'{v.replace(chr(39), chr(39)*2)}'" if v is not None else 'NULL',
    'JSON': lambda v: f"'{v.replace(chr(39), chr(39)*2)}'" if v is not None else 'NULL',
}

# Tables that need sequence reset after import
TABLES_WITH_SEQUENCES = [
    'user',
    'pipelines',
    'pipeline_stages',
    'people',
    'contacts',
    'tasks',
    'notes',
    # Add other tables with serial/identity columns
]

@contextmanager
def connect_sqlite():
    """Context manager for SQLite connection"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def connect_pg():
    """Context manager for PostgreSQL connection"""
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    try:
        yield conn
    finally:
        conn.close()

def get_table_info(sqlite_conn, table_name):
    """Get column information for a table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return {col['name']: col['type'] for col in columns}

def get_row_count(conn, table_name, is_sqlite=True):
    """Get the number of rows in a table"""
    cursor = conn.cursor()
    if is_sqlite:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    else:
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
    return cursor.fetchone()[0]

def map_sqlite_to_pg_type(sqlite_type):
    """Map SQLite type to PostgreSQL type for transformations"""
    sqlite_type = sqlite_type.upper()
    if 'INT' in sqlite_type:
        return 'INTEGER'
    elif sqlite_type in ('TEXT', 'VARCHAR', 'CHAR', 'CLOB'):
        return 'TEXT'
    elif sqlite_type in ('REAL', 'FLOAT', 'DOUBLE'):
        return 'REAL'
    elif sqlite_type == 'BOOLEAN':
        return 'BOOLEAN'
    elif 'TIMESTAMP' in sqlite_type or 'DATETIME' in sqlite_type:
        return 'TIMESTAMP'
    elif 'JSON' in sqlite_type:
        return 'JSON'
    else:
        return 'TEXT'  # Default to text for unknown types

def transform_value(value, sqlite_type):
    """Transform a value based on its SQLite type to PostgreSQL compatible format"""
    pg_type = map_sqlite_to_pg_type(sqlite_type)
    if pg_type in TYPE_MAPPINGS:
        return TYPE_MAPPINGS[pg_type](value)
    return f"'{value}'" if value is not None else 'NULL'

def migrate_table(sqlite_conn, pg_conn, table_name, batch_size=BATCH_SIZE, dry_run=False):
    """Migrate data from SQLite table to PostgreSQL table"""
    print(f"\nMigrating table: {table_name}")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get column information
    columns_info = get_table_info(sqlite_conn, table_name)
    columns = list(columns_info.keys())
    
    # Count rows for progress reporting
    total_rows = get_row_count(sqlite_conn, table_name)
    if total_rows == 0:
        print(f"  No data to migrate for table {table_name}")
        return 0
    
    print(f"  Total rows to migrate: {total_rows}")
    
    # Prepare column identifiers for PostgreSQL
    pg_columns = sql.SQL(', ').join(sql.Identifier(col) for col in columns)
    
    # If not dry run, disable triggers and truncate table
    if not dry_run:
        pg_cursor.execute(
            sql.SQL("ALTER TABLE {} DISABLE TRIGGER ALL").format(sql.Identifier(table_name))
        )
        pg_cursor.execute(
            sql.SQL("TRUNCATE TABLE {} CASCADE").format(sql.Identifier(table_name))
        )
    
    # Process in batches
    offset = 0
    migrated_count = 0
    start_time = time.time()
    
    while offset < total_rows:
        sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            break
        
        # Process each batch
        for row in rows:
            values = []
            for col in columns:
                sqlite_type = columns_info[col]
                value = row[col]
                values.append(transform_value(value, sqlite_type))
            
            # Construct and execute INSERT statement
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)})"
            
            if dry_run:
                print(f"  Would execute: {insert_sql}")
            else:
                try:
                    pg_cursor.execute(insert_sql)
                except Exception as e:
                    print(f"Error inserting row {migrated_count + 1}: {e}")
                    print(f"SQL: {insert_sql}")
                    raise
            
            migrated_count += 1
        
        # Commit batch
        if not dry_run:
            pg_conn.commit()
        
        # Update progress
        offset += batch_size
        elapsed = time.time() - start_time
        rows_per_sec = migrated_count / elapsed if elapsed > 0 else 0
        percent_complete = min(100, (migrated_count / total_rows) * 100)
        print(f"  Progress: {migrated_count}/{total_rows} rows ({percent_complete:.1f}%) - {rows_per_sec:.1f} rows/sec")
    
    # Re-enable triggers
    if not dry_run:
        pg_cursor.execute(
            sql.SQL("ALTER TABLE {} ENABLE TRIGGER ALL").format(sql.Identifier(table_name))
        )
        pg_conn.commit()
    
    print(f"  Completed: {migrated_count} rows migrated")
    return migrated_count

def reset_sequences(pg_conn, dry_run=False):
    """Reset sequences for tables with identity/serial columns"""
    print("\nResetting sequences")
    
    pg_cursor = pg_conn.cursor()
    
    for table in TABLES_WITH_SEQUENCES:
        # Find the primary key column
        pg_cursor.execute("""
            SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
            FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE  i.indrelid = %s::regclass
            AND    i.indisprimary
        """, (table,))
        
        pk_column_info = pg_cursor.fetchone()
        if not pk_column_info:
            print(f"  Warning: No primary key found for table {table}")
            continue
        
        pk_column, data_type = pk_column_info
        
        # Check if sequence exists
        pg_cursor.execute("""
            SELECT pg_get_serial_sequence(%s, %s) as sequence_name
        """, (table, pk_column))
        
        sequence_info = pg_cursor.fetchone()
        sequence_name = sequence_info[0] if sequence_info and sequence_info[0] else None
        
        if not sequence_name:
            print(f"  Warning: No sequence found for {table}.{pk_column}")
            continue
        
        if dry_run:
            print(f"  Would reset sequence {sequence_name} for table {table}")
        else:
            # Set sequence value to max + 1
            reset_sql = f"""
                SELECT setval('{sequence_name}', COALESCE(
                    (SELECT MAX({pk_column}) FROM {table}), 0
                ) + 1, false)
            """
            pg_cursor.execute(reset_sql)
            pg_conn.commit()
            print(f"  Reset sequence {sequence_name} for table {table}")

def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description='Migrate data from SQLite to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Preview migration without making changes')
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made to the database")
    
    if not PG_CONNECTION_STRING:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"ERROR: SQLite database not found at {SQLITE_DB_PATH}")
        sys.exit(1)
    
    # Create migration report file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"migration_report_{timestamp}.txt"
    
    with open(report_file, 'w') as report:
        report.write(f"Migration Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.write(f"SQLite DB: {SQLITE_DB_PATH}\n")
        report.write(f"PostgreSQL: {PG_CONNECTION_STRING}\n")
        report.write(f"Dry Run: {'Yes' if args.dry_run else 'No'}\n\n")
        
        start_time = time.time()
        total_migrated = 0
        
        try:
            with connect_sqlite() as sqlite_conn, connect_pg() as pg_conn:
                for table in TABLES_IN_ORDER:
                    sqlite_count = get_row_count(sqlite_conn, table)
                    
                    table_start = time.time()
                    rows_migrated = migrate_table(sqlite_conn, pg_conn, table, BATCH_SIZE, args.dry_run)
                    table_time = time.time() - table_start
                    
                    total_migrated += rows_migrated
                    
                    # Log table migration result
                    report.write(f"Table: {table}\n")
                    report.write(f"  Source count: {sqlite_count}\n")
                    report.write(f"  Migrated count: {rows_migrated}\n")
                    report.write(f"  Time: {table_time:.2f} seconds\n\n")
                
                # Reset sequences after migration
                if not args.dry_run:
                    reset_sequences(pg_conn, args.dry_run)
                
                # Compare row counts
                report.write("Row Count Comparison:\n")
                with pg_conn.cursor() as pg_cursor:
                    for table in TABLES_IN_ORDER:
                        sqlite_count = get_row_count(sqlite_conn, table)
                        
                        if not args.dry_run:
                            pg_count = get_row_count(pg_conn, table, False)
                        else:
                            pg_count = 0
                        
                        report.write(f"  {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}\n")
                        
                        if not args.dry_run and sqlite_count != pg_count:
                            report.write(f"  WARNING: Count mismatch for table {table}\n")
            
            total_time = time.time() - start_time
            report.write(f"\nTotal rows migrated: {total_migrated}\n")
            report.write(f"Total migration time: {total_time:.2f} seconds\n")
            
            print(f"\nMigration completed in {total_time:.2f} seconds")
            print(f"Total rows migrated: {total_migrated}")
            print(f"Migration report written to {report_file}")
            
            if not args.dry_run:
                print("\nNext steps:")
                print("1. Run post-migration validation: python post_migration_checks.py")
                print("2. Update your application to use the PostgreSQL database")
        
        except Exception as e:
            report.write(f"\nERROR: Migration failed: {str(e)}\n")
            print(f"Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    main() 