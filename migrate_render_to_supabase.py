#!/usr/bin/env python3
"""
Render PostgreSQL to Supabase PostgreSQL Migration Script for Mobilize CRM

This script migrates data from an existing Render PostgreSQL database to 
a Supabase PostgreSQL database, handling schema differences and preserving relationships.

Usage:
    python migrate_render_to_supabase.py [--dry-run] [--table TABLE_NAME]

Arguments:
    --dry-run: Optional flag to preview migration without making changes
    --table: Optional specific table to migrate (otherwise migrates all tables)
"""

import os
import sys
import time
import argparse
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from datetime import datetime
from contextlib import contextmanager
import json
import importlib.util

# Load environment variables
load_dotenv()
load_dotenv('.env.production', override=True)

# Configuration
RENDER_DB_URL = os.getenv('RENDER_DB_URL')
SUPABASE_DB_URL = os.getenv('DATABASE_URL')
BATCH_SIZE = 500  # Number of records to process in each batch

# Try to import mappings from migration_mappings.py if it exists
try:
    if os.path.exists('migration_mappings.py'):
        spec = importlib.util.spec_from_file_location("migration_mappings", "migration_mappings.py")
        mappings_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mappings_module)
        
        # Import table order
        if hasattr(mappings_module, 'TABLES_IN_ORDER'):
            TABLES_IN_ORDER = mappings_module.TABLES_IN_ORDER
        else:
            # Default table order if not defined in migration_mappings.py
            TABLES_IN_ORDER = [
                'users',
                'offices',
                'pipelines',
                'pipeline_stages',
                'people',
                'contacts',
                'pipeline_contacts',
                'pipeline_stage_history',
                'tasks',
                'notes',
                'churches',
                'communications',
                'phone_numbers',
                'addresses',
                'google_tokens',
                'email_templates',
                'email_signatures',
                'email_campaigns',
                'email_tracking',
            ]
        
        # Import other mappings
        COLUMN_MAPPINGS = getattr(mappings_module, 'COLUMN_MAPPINGS', {})
        EXCLUDE_COLUMNS = getattr(mappings_module, 'EXCLUDE_COLUMNS', {})
        SKIP_TABLES = getattr(mappings_module, 'SKIP_TABLES', ['alembic_version'])
        COLUMN_TRANSFORMATIONS = getattr(mappings_module, 'COLUMN_TRANSFORMATIONS', {})
        TABLE_MAPPINGS = getattr(mappings_module, 'TABLE_MAPPINGS', {})
        CUSTOM_SQL_TRANSFORMS = getattr(mappings_module, 'CUSTOM_SQL_TRANSFORMS', {})
    else:
        # Default mappings if migration_mappings.py doesn't exist
        TABLES_IN_ORDER = [
            'users',
            'offices',
            'pipelines',
            'pipeline_stages',
            'people',
            'contacts',
            'pipeline_contacts',
            'pipeline_stage_history',
            'tasks',
            'notes',
            'churches',
            'communications',
            'phone_numbers',
            'addresses',
            'google_tokens',
            'email_templates',
            'email_signatures',
            'email_campaigns',
            'email_tracking',
        ]
        COLUMN_MAPPINGS = {}
        EXCLUDE_COLUMNS = {}
        SKIP_TABLES = ['alembic_version']
        COLUMN_TRANSFORMATIONS = {}
        TABLE_MAPPINGS = {}
        CUSTOM_SQL_TRANSFORMS = {}
except Exception as e:
    print(f"Warning: Failed to import mappings from migration_mappings.py: {e}")
    print("Using default mappings instead")
    
    # Default mappings if import fails
    TABLES_IN_ORDER = [
        'users',
        'offices',
        'pipelines',
        'pipeline_stages',
        'people',
        'contacts',
        'pipeline_contacts',
        'pipeline_stage_history',
        'tasks',
        'notes',
        'churches',
        'communications',
        'phone_numbers',
        'addresses',
        'google_tokens',
        'email_templates',
        'email_signatures',
        'email_campaigns',
        'email_tracking',
    ]
    COLUMN_MAPPINGS = {}
    EXCLUDE_COLUMNS = {}
    SKIP_TABLES = ['alembic_version']
    COLUMN_TRANSFORMATIONS = {}
    TABLE_MAPPINGS = {}
    CUSTOM_SQL_TRANSFORMS = {}

@contextmanager
def connect_render():
    """Context manager for Render PostgreSQL connection"""
    if not RENDER_DB_URL:
        raise ValueError("RENDER_DB_URL environment variable not set")
        
    conn = psycopg2.connect(RENDER_DB_URL)
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def connect_supabase():
    """Context manager for Supabase PostgreSQL connection"""
    if not SUPABASE_DB_URL:
        raise ValueError("DATABASE_URL environment variable not set")
        
    conn = psycopg2.connect(SUPABASE_DB_URL)
    try:
        yield conn
    finally:
        conn.close()

def get_table_schema(conn, table_name):
    """Get column information for a table"""
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

def get_column_names(conn, table_name):
    """Get list of column names for a table"""
    schema = get_table_schema(conn, table_name)
    return [col['column_name'] for col in schema]

def get_primary_key(conn, table_name):
    """Get the primary key column(s) for a table"""
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("""
        SELECT c.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
        JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
            AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = %s
        ORDER BY c.ordinal_position
    """, (table_name,))
    primary_keys = [row['column_name'] for row in cursor.fetchall()]
    cursor.close()
    return primary_keys

def get_row_count(conn, table_name):
    """Get the number of rows in a table"""
    cursor = conn.cursor()
    cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def truncate_table(conn, table_name):
    """Truncate a target table, disabling triggers temporarily"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            sql.SQL("ALTER TABLE {} DISABLE TRIGGER ALL").format(sql.Identifier(table_name))
        )
        cursor.execute(
            sql.SQL("TRUNCATE TABLE {} CASCADE").format(sql.Identifier(table_name))
        )
        cursor.execute(
            sql.SQL("ALTER TABLE {} ENABLE TRIGGER ALL").format(sql.Identifier(table_name))
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error truncating table {table_name}: {e}")
        raise
    finally:
        cursor.close()

def map_columns(source_columns, target_columns, table_name):
    """Map source columns to target columns based on COLUMN_MAPPINGS"""
    column_map = {}
    
    # Get column mapping for this table
    table_mapping = COLUMN_MAPPINGS.get(table_name, {})
    
    # Get exclude columns for this table
    exclude_cols = EXCLUDE_COLUMNS.get(table_name, [])
    
    for col in source_columns:
        # Skip excluded columns
        if col in exclude_cols:
            continue
            
        # Apply mapping if exists
        target_col = table_mapping.get(col, col)
        
        # Only include column if it exists in target
        if target_col in target_columns:
            column_map[col] = target_col
    
    return column_map

def transform_value(table_name, column_name, value):
    """Apply custom transformations to column values if defined"""
    # Get transformations for this table
    table_transformations = COLUMN_TRANSFORMATIONS.get(table_name, {})
    
    # Apply transformation if exists for this column
    if column_name in table_transformations:
        transform_func = table_transformations[column_name]
        try:
            return transform_func(value)
        except Exception as e:
            print(f"Error applying transformation to {table_name}.{column_name}: {e}")
            return value
    
    # Default handling for common data types
    if isinstance(value, dict) or isinstance(value, list):
        return json.dumps(value)
    
    return value

def migrate_table(render_conn, supabase_conn, render_table, batch_size=BATCH_SIZE, dry_run=False):
    """Migrate data from Render table to Supabase table"""
    start_time = time.time()
    print(f"\nMigrating table: {render_table}")
    
    # Get target table name from mappings if it exists
    target_table = TABLE_MAPPINGS.get(render_table, render_table)
    print(f"Target table: {target_table}")
    
    # Handle custom SQL transforms if defined
    if target_table in CUSTOM_SQL_TRANSFORMS and not dry_run:
        print(f"Using custom SQL transform for {target_table}")
        sql_transform = CUSTOM_SQL_TRANSFORMS[target_table].format(render_table=render_table)
        cursor = supabase_conn.cursor()
        try:
            cursor.execute(sql_transform)
            supabase_conn.commit()
            print(f"Custom SQL transform completed successfully")
            return
        except Exception as e:
            supabase_conn.rollback()
            print(f"Error executing custom SQL transform: {e}")
            return
    
    # Get render table columns
    try:
        render_columns = get_column_names(render_conn, render_table)
    except Exception as e:
        print(f"Error getting columns for Render table '{render_table}': {e}")
        return
    
    # Get supabase table columns
    try:
        supabase_columns = get_column_names(supabase_conn, target_table)
    except Exception as e:
        print(f"Error getting columns for Supabase table '{target_table}': {e}")
        return
    
    # Map columns between tables
    mapped_columns = map_columns(render_columns, supabase_columns, render_table)
    if not mapped_columns:
        print(f"No mappable columns found between {render_table} and {target_table}")
        return
    
    # Get column names from the mapping (source and target)
    source_columns = list(mapped_columns.keys())
    target_columns = list(mapped_columns.values())
    
    # Get total row count for progress tracking
    try:
        render_count = get_row_count(render_conn, render_table)
        print(f"Total rows in source table: {render_count}")
    except Exception as e:
        print(f"Error getting row count: {e}")
        return
    
    if render_count == 0:
        print(f"Source table is empty. Skipping.")
        return
    
    # Get existing row count in target table
    try:
        existing_count = get_row_count(supabase_conn, target_table)
        print(f"Existing rows in target table: {existing_count}")
    except Exception as e:
        print(f"Error getting existing row count: {e}")
        return
    
    # Generate SQL for data retrieval
    source_sql = sql.SQL("SELECT {} FROM {}").format(
        sql.SQL(', ').join(map(sql.Identifier, source_columns)),
        sql.Identifier(render_table)
    )
    
    # Create insert SQL
    insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
        sql.Identifier(target_table),
        sql.SQL(', ').join(map(sql.Identifier, target_columns)),
        sql.SQL(', ').join(sql.Placeholder() * len(target_columns))
    )
    
    # Prepare to fetch data in batches
    with render_conn.cursor() as render_cursor:
        render_cursor.execute(source_sql)
        
        total_processed = 0
        total_inserted = 0
        batch_num = 0
        
        while True:
            batch = render_cursor.fetchmany(batch_size)
            if not batch:
                break
                
            batch_num += 1
            print(f"Processing batch {batch_num} ({len(batch)} rows)...")
            
            # Process the batch
            with supabase_conn.cursor() as supabase_cursor:
                for row in batch:
                    total_processed += 1
                    
                    # Transform values according to mappings
                    values = []
                    for i, col in enumerate(source_columns):
                        value = row[i]
                        # Apply custom transformations if defined
                        value = transform_value(render_table, col, value)
                        values.append(value)
                    
                    # Execute insert if not in dry run mode
                    if not dry_run:
                        try:
                            supabase_cursor.execute(insert_sql, values)
                            total_inserted += 1
                        except Exception as e:
                            print(f"Error inserting row: {e}")
                            print(f"Values: {values}")
                    else:
                        total_inserted += 1
                        
                if not dry_run:
                    supabase_conn.commit()
            
            # Print progress
            progress = (total_processed / render_count) * 100
            print(f"Progress: {progress:.1f}% ({total_processed}/{render_count})")
    
    # Reset sequences in target table if not in dry run mode
    if not dry_run:
        try:
            reset_sequence(supabase_conn, target_table)
        except Exception as e:
            print(f"Warning: Could not reset sequence for {target_table}: {e}")
    
    # Report results
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"\nMigration of {render_table} to {target_table} completed:")
    print(f"- Processed: {total_processed} rows")
    print(f"- Inserted: {total_inserted} rows")
    print(f"- Elapsed time: {elapsed:.2f} seconds")
    
    # Verify row count if not in dry run mode
    if not dry_run:
        verify_count = get_row_count(supabase_conn, target_table)
        print(f"- Final row count in target table: {verify_count}")
        new_rows = verify_count - existing_count
        print(f"- Net new rows: {new_rows}")
    
    return total_inserted

def reset_sequence(conn, table_name):
    """Reset sequence for a table with serial/identity column"""
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    try:
        # Find primary key column
        primary_keys = get_primary_key(conn, table_name)
        if not primary_keys:
            print(f"  Warning: No primary key found for table {table_name}")
            return
        
        # Check if primary key has a sequence
        for pk in primary_keys:
            cursor.execute("""
                SELECT pg_get_serial_sequence(%s, %s) as sequence_name
            """, (table_name, pk))
            
            sequence_info = cursor.fetchone()
            sequence_name = sequence_info['sequence_name'] if sequence_info and sequence_info['sequence_name'] else None
            
            if sequence_name:
                # Set sequence value to max + 1
                reset_sql = f"""
                    SELECT setval('{sequence_name}', COALESCE(
                        (SELECT MAX({pk}) FROM {table_name}), 0
                    ) + 1, false)
                """
                cursor.execute(reset_sql)
                conn.commit()
                print(f"  Reset sequence {sequence_name} for {table_name}.{pk}")
    except Exception as e:
        print(f"Error resetting sequence for table {table_name}: {e}")
    finally:
        cursor.close()

def reset_all_sequences(conn):
    """Reset sequences for all tables with identity/serial columns"""
    print("\nResetting sequences")
    
    for table in TABLES_IN_ORDER:
        if table in SKIP_TABLES:
            continue
        reset_sequence(conn, table)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Migrate data from Render PostgreSQL to Supabase PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Preview migration without making changes")
    parser.add_argument("--table", help="Specific table to migrate")
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made to the database")
    
    # Check for valid connection strings
    if not RENDER_DB_URL:
        print("Error: RENDER_DB_URL environment variable not set")
        sys.exit(1)
    
    if not SUPABASE_DB_URL:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Connect to databases
    try:
        with connect_render() as render_conn, connect_supabase() as supabase_conn:
            # If specific table is specified, only migrate that table
            if args.table:
                if args.table in SKIP_TABLES:
                    print(f"Skipping table {args.table} as it's in the skip list")
                else:
                    migrate_table(render_conn, supabase_conn, args.table, dry_run=args.dry_run)
            else:
                # Get list of tables to migrate
                tables_to_migrate = TABLES_IN_ORDER
                
                # Migrate each table in order
                total_migrated = 0
                for table in tables_to_migrate:
                    if table in SKIP_TABLES:
                        print(f"Skipping table {table} as it's in the skip list")
                        continue
                    
                    try:
                        # Check if source table exists in Render database
                        render_count = get_row_count(render_conn, table)
                        
                        # Migrate table
                        rows_migrated = migrate_table(render_conn, supabase_conn, table, dry_run=args.dry_run)
                        if rows_migrated:
                            total_migrated += rows_migrated
                    except Exception as e:
                        print(f"Error migrating table {table}: {e}")
                
                # Report total migration results
                print("\nMigration Summary:")
                print(f"Total rows migrated: {total_migrated}")
                
                if not args.dry_run:
                    # Reset all sequences to ensure correct auto-increment values
                    try:
                        reset_all_sequences(supabase_conn)
                    except Exception as e:
                        print(f"Warning: Error resetting sequences: {e}")
                    
                    print("\nMigration completed successfully.")
                    print("Please update your application connection strings to use Supabase.")
                else:
                    print("\nDry run completed. No changes were made to the target database.")
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 