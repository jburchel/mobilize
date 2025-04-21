#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Tool for Mobilize CRM

This script migrates data from a local SQLite database to PostgreSQL for production deployment.
It preserves all relationships and handles schema differences between SQLite and PostgreSQL.

Usage:
    python sqlite_to_postgres_migrate.py [--dry-run] [--table TABLE_NAME]

Arguments:
    --dry-run: Optional flag to preview migration without making changes
    --table: Optional specific table to migrate (otherwise migrates all tables)
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import execute_values, DictCursor
from dotenv import load_dotenv
import argparse
from contextlib import contextmanager
import json
import time
from datetime import datetime

# Load environment variables
load_dotenv()
load_dotenv('.env.production', override=True)

# Configuration
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'instance/mobilize_crm.db')
PG_DB_URL = os.getenv('DATABASE_URL')
BATCH_SIZE = 500  # Number of records to process in each batch

# Tables in dependency order (for foreign key constraints)
TABLES_IN_ORDER = [
    'permissions',
    'roles',
    'offices',
    'users',
    'contacts',
    'people',
    'churches',
    'pipelines',
    'pipeline_stages',
    'pipeline_contacts',
    'pipeline_stage_history',
    'tasks',
    'communications',
    'google_tokens',
    'email_templates',
    'email_signatures',
    'email_campaigns',
    'email_tracking'
]

# Tables to skip during migration
SKIP_TABLES = ['alembic_version', 'sqlite_sequence']

# Type conversion mappings for SQLite to PostgreSQL
TYPE_CONVERSIONS = {
    'BOOLEAN': lambda v: bool(v) if v is not None else None,
    'INTEGER': lambda v: int(v) if v is not None else None,
    'FLOAT': lambda v: float(v) if v is not None else None,
    'TEXT': lambda v: str(v) if v is not None else None,
    'TIMESTAMP': lambda v: v  # PostgreSQL will handle valid timestamp formats
}

@contextmanager
def connect_sqlite():
    """Context manager for SQLite connection"""
    if not os.path.exists(SQLITE_DB_PATH):
        raise ValueError(f"SQLite database not found at: {SQLITE_DB_PATH}")
        
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def connect_postgres():
    """Context manager for PostgreSQL connection"""
    if not PG_DB_URL:
        raise ValueError("DATABASE_URL environment variable not set")
        
    conn = psycopg2.connect(PG_DB_URL)
    try:
        yield conn
    finally:
        conn.close()

def get_sqlite_tables(conn):
    """Get all table names from SQLite database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sqlite_sequence', 'alembic_version')")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_sqlite_table_schema(conn, table_name):
    """Get column information for a SQLite table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    cursor.close()
    return columns

def get_postgres_table_schema(conn, table_name):
    """Get column information for a PostgreSQL table"""
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = cursor.fetchall()
    cursor.close()
    return columns

def get_column_names(schema):
    """Extract column names from schema"""
    if isinstance(schema[0], sqlite3.Row):
        # SQLite schema
        return [col['name'] for col in schema]
    else:
        # PostgreSQL schema
        return [col['column_name'] for col in schema]

def get_column_data_types(conn, table_name):
    """Get data types for PostgreSQL columns"""
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
    """, (table_name,))
    types = {row['column_name']: row['data_type'].upper() for row in cursor.fetchall()}
    cursor.close()
    return types

def convert_value(value, data_type):
    """Convert value to appropriate type for PostgreSQL"""
    if value is None:
        return None
        
    # Determine the general type for conversion
    if data_type.startswith('VARCHAR') or data_type.startswith('TEXT') or data_type.startswith('CHAR'):
        pg_type = 'TEXT'
    elif data_type.startswith('INT') or data_type == 'BIGINT' or data_type == 'SMALLINT':
        pg_type = 'INTEGER'
    elif data_type.startswith('BOOL'):
        pg_type = 'BOOLEAN'
    elif data_type.startswith('FLOAT') or data_type.startswith('DOUBLE') or data_type == 'REAL' or data_type == 'NUMERIC':
        pg_type = 'FLOAT'
    elif data_type.startswith('TIMESTAMP') or data_type.startswith('DATE'):
        pg_type = 'TIMESTAMP'
    else:
        pg_type = 'TEXT'  # Default to text for unsupported types
    
    # Apply conversion
    conversion_func = TYPE_CONVERSIONS.get(pg_type, lambda x: x)
    try:
        return conversion_func(value)
    except (ValueError, TypeError) as e:
        print(f"Warning: Could not convert value '{value}' to {pg_type}: {e}")
        return None

def get_row_count(conn, table_name):
    """Get number of rows in a table"""
    if isinstance(conn, sqlite3.Connection):
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    else:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
    
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def disable_triggers(conn, table_name):
    """Temporarily disable triggers on PostgreSQL table"""
    cursor = conn.cursor()
    try:
        cursor.execute(f'ALTER TABLE "{table_name}" DISABLE TRIGGER ALL')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Warning: Could not disable triggers on {table_name}: {e}")
    finally:
        cursor.close()

def enable_triggers(conn, table_name):
    """Re-enable triggers on PostgreSQL table"""
    cursor = conn.cursor()
    try:
        cursor.execute(f'ALTER TABLE "{table_name}" ENABLE TRIGGER ALL')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Warning: Could not re-enable triggers on {table_name}: {e}")
    finally:
        cursor.close()

def migrate_table(sqlite_conn, pg_conn, table_name, batch_size=BATCH_SIZE, dry_run=False):
    """Migrate data from SQLite table to PostgreSQL table"""
    start_time = time.time()
    
    # Get schemas
    sqlite_schema = get_sqlite_table_schema(sqlite_conn, table_name)
    
    try:
        pg_schema = get_postgres_table_schema(pg_conn, table_name)
    except psycopg2.errors.UndefinedTable:
        print(f"Table {table_name} does not exist in PostgreSQL database. Skipping.")
        return 0
    
    # Get column names
    sqlite_columns = get_column_names(sqlite_schema)
    pg_columns = get_column_names(pg_schema)
    
    # Find common columns
    common_columns = [col for col in sqlite_columns if col in pg_columns]
    if not common_columns:
        print(f"No matching columns found for table {table_name}. Skipping.")
        return 0
    
    # Build column list for queries
    sqlite_cols_str = ', '.join([f'"{col}"' for col in common_columns])
    pg_cols_str = ', '.join([f'"{col}"' for col in common_columns])
    
    # Get row count
    total_rows = get_row_count(sqlite_conn, table_name)
    if total_rows == 0:
        print(f"No data in table {table_name}. Skipping.")
        return 0
    
    print(f"\nMigrating {total_rows} rows from {table_name}")
    
    # Get PostgreSQL column data types
    pg_column_types = get_column_data_types(pg_conn, table_name)
    
    # Prepare for migration
    offset = 0
    migrated_rows = 0
    
    if not dry_run:
        # Disable triggers temporarily
        disable_triggers(pg_conn, table_name)
    
    while offset < total_rows:
        # Fetch batch of data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f'SELECT {sqlite_cols_str} FROM "{table_name}" LIMIT {batch_size} OFFSET {offset}')
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            break
        
        # Convert rows to list of dictionaries
        row_dicts = [dict(row) for row in rows]
        
        # Convert data types for PostgreSQL
        pg_data = []
        for row in row_dicts:
            pg_row = []
            for col in common_columns:
                value = row[col]
                if col in pg_column_types:
                    # Convert to proper type
                    value = convert_value(value, pg_column_types[col])
                pg_row.append(value)
            pg_data.append(tuple(pg_row))
        
        if not dry_run:
            # Insert data into PostgreSQL
            pg_cursor = pg_conn.cursor()
            placeholders = ', '.join(['%s'] * len(common_columns))
            try:
                execute_values(
                    pg_cursor,
                    f'INSERT INTO "{table_name}" ({pg_cols_str}) VALUES %s ON CONFLICT DO NOTHING',
                    pg_data
                )
                pg_conn.commit()
                migrated_rows += len(pg_data)
            except Exception as e:
                pg_conn.rollback()
                print(f"Error inserting data into {table_name}: {e}")
                print(f"Problematic data: {pg_data[:1]}")  # Print just the first row for debugging
                raise
            finally:
                pg_cursor.close()
        else:
            # In dry-run mode, just count rows
            migrated_rows += len(pg_data)
            print(f"Would migrate {len(pg_data)} rows to {table_name} (dry run)")
        
        # Update offset for next batch
        offset += batch_size
        
        # Print progress
        progress = min(offset, total_rows) / total_rows * 100
        print(f"Progress: {progress:.1f}% ({min(offset, total_rows)}/{total_rows})", end='\r')
        
    print(f"\nMigrated {migrated_rows} rows to {table_name} in {time.time() - start_time:.2f} seconds")
    
    if not dry_run:
        # Re-enable triggers
        enable_triggers(pg_conn, table_name)
        
        # Update sequence if the table has an ID column
        reset_sequence(pg_conn, table_name)
    
    return migrated_rows

def reset_sequence(conn, table_name):
    """Reset the autoincrement sequence for a table"""
    cursor = conn.cursor()
    try:
        # Check if the table has an id column that's a serial/identity
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            AND column_name = 'id'
            AND (column_default LIKE 'nextval%%' OR is_identity = 'YES')
        """, (table_name,))
        
        if cursor.fetchone():
            cursor.execute(f"""
                SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), 
                COALESCE((SELECT MAX(id) FROM "{table_name}"), 1))
            """)
            conn.commit()
            print(f"Reset sequence for {table_name}")
    except Exception as e:
        conn.rollback()
        print(f"Warning: Could not reset sequence for {table_name}: {e}")
    finally:
        cursor.close()

def enable_foreign_keys(conn, enabled=True):
    """Enable or disable foreign key constraints in PostgreSQL"""
    cursor = conn.cursor()
    try:
        mode = 'origin' if enabled else 'replica'
        cursor.execute(f"SET session_replication_role = '{mode}'")
        conn.commit()
        status = "enabled" if enabled else "disabled"
        print(f"Foreign key constraints {status}")
    except Exception as e:
        conn.rollback()
        print(f"Warning: Could not change foreign key constraint mode: {e}")
    finally:
        cursor.close()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Migrate data from SQLite to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Preview migration without making changes')
    parser.add_argument('--table', help='Specific table to migrate')
    parser.add_argument('--sqlite-path', help='Path to SQLite database file')
    args = parser.parse_args()
    
    # Update SQLite path if provided
    global SQLITE_DB_PATH
    if args.sqlite_path:
        SQLITE_DB_PATH = args.sqlite_path
    
    print(f"SQLite database: {SQLITE_DB_PATH}")
    print(f"PostgreSQL database: {PG_DB_URL}")
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made to the PostgreSQL database")
    
    # Connect to databases
    try:
        with connect_sqlite() as sqlite_conn, connect_postgres() as pg_conn:
            # Disable foreign key constraints for the migration
            if not args.dry_run:
                enable_foreign_keys(pg_conn, False)
            
            # Get all tables if specific table not specified
            if args.table:
                tables_to_migrate = [args.table]
            else:
                tables_to_migrate = []
                
                # Use predefined order if available
                for table in TABLES_IN_ORDER:
                    if table not in SKIP_TABLES:
                        tables_to_migrate.append(table)
                
                # Add any remaining tables from SQLite
                sqlite_tables = get_sqlite_tables(sqlite_conn)
                for table in sqlite_tables:
                    if table not in tables_to_migrate and table not in SKIP_TABLES:
                        tables_to_migrate.append(table)
            
            # Migrate each table
            total_migrated = 0
            start_time = time.time()
            
            for table in tables_to_migrate:
                try:
                    rows = migrate_table(sqlite_conn, pg_conn, table, BATCH_SIZE, args.dry_run)
                    total_migrated += rows
                except Exception as e:
                    print(f"Error migrating table {table}: {e}")
                    if not args.dry_run:
                        # Re-enable foreign keys before exiting
                        enable_foreign_keys(pg_conn, True)
                    raise
            
            # Re-enable foreign key constraints
            if not args.dry_run:
                enable_foreign_keys(pg_conn, True)
            
            # Print summary
            total_time = time.time() - start_time
            print("\n=== Migration Summary ===")
            print(f"Total rows migrated: {total_migrated}")
            print(f"Total tables migrated: {len(tables_to_migrate)}")
            print(f"Total time: {total_time:.2f} seconds")
            
            if args.dry_run:
                print("\nThis was a dry run. No data was actually migrated.")
    
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 