#!/usr/bin/env python3
import os
import sys
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from tabulate import tabulate

def get_sqlite_schema(sqlite_db_path):
    """Get schema information from SQLite database."""
    if not os.path.exists(sqlite_db_path):
        print(f"Error: SQLite database file not found at {sqlite_db_path}")
        return None
    
    try:
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema_info = {}
        
        for table in tables:
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [{
                'name': row[1],
                'type': row[2],
                'notnull': row[3],
                'default': row[4],
                'pk': row[5]
            } for row in cursor.fetchall()]
            
            schema_info[table] = columns
        
        conn.close()
        return schema_info
    except Exception as e:
        print(f"Error getting SQLite schema: {str(e)}")
        return None

def get_postgres_schema(connection_string):
    """Get schema information from PostgreSQL database."""
    try:
        conn = psycopg2.connect(connection_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Get list of tables in public schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE';
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        schema_info = {}
        
        for table in tables:
            # Get column info for each table
            cursor.execute(f"""
                SELECT 
                    column_name, 
                    data_type, 
                    CASE WHEN is_nullable = 'NO' THEN 1 ELSE 0 END as notnull,
                    column_default,
                    CASE WHEN column_name IN (
                        SELECT column_name 
                        FROM information_schema.table_constraints tc 
                        JOIN information_schema.constraint_column_usage ccu 
                        ON tc.constraint_name = ccu.constraint_name 
                        WHERE tc.constraint_type = 'PRIMARY KEY' 
                        AND tc.table_name = '{table}'
                    ) THEN 1 ELSE 0 END as pk
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND table_schema = 'public';
            """)
            
            columns = [{
                'name': row[0],
                'type': row[1],
                'notnull': row[2],
                'default': row[3],
                'pk': row[4]
            } for row in cursor.fetchall()]
            
            schema_info[table] = columns
        
        cursor.close()
        conn.close()
        return schema_info
    except Exception as e:
        print(f"Error getting PostgreSQL schema: {str(e)}")
        return None

def compare_schemas(sqlite_schema, postgres_schema):
    """Compare SQLite and PostgreSQL schemas and identify differences."""
    if not sqlite_schema or not postgres_schema:
        return None
    
    comparison_results = {
        'missing_tables': [],
        'missing_columns': [],
        'type_differences': []
    }
    
    # Check for missing tables
    sqlite_tables = set(sqlite_schema.keys())
    postgres_tables = set(postgres_schema.keys())
    
    missing_tables = sqlite_tables - postgres_tables
    if missing_tables:
        comparison_results['missing_tables'] = list(missing_tables)
    
    # Check for missing columns and type differences
    for table in sqlite_tables.intersection(postgres_tables):
        sqlite_columns = {col['name']: col for col in sqlite_schema[table]}
        postgres_columns = {col['name']: col for col in postgres_schema[table]}
        
        sqlite_column_names = set(sqlite_columns.keys())
        postgres_column_names = set(postgres_columns.keys())
        
        missing_columns = sqlite_column_names - postgres_column_names
        if missing_columns:
            for col_name in missing_columns:
                comparison_results['missing_columns'].append({
                    'table': table,
                    'column': col_name,
                    'sqlite_type': sqlite_columns[col_name]['type']
                })
        
        # Check for type differences
        for col_name in sqlite_column_names.intersection(postgres_column_names):
            sqlite_type = sqlite_columns[col_name]['type'].lower()
            postgres_type = postgres_columns[col_name]['type'].lower()
            
            # Map SQLite types to PostgreSQL types for comparison
            sqlite_to_postgres_type_map = {
                'integer': ['integer', 'int', 'int4', 'bigint', 'int8'],
                'text': ['text', 'character varying', 'varchar'],
                'real': ['real', 'double precision', 'float8'],
                'blob': ['bytea'],
                'boolean': ['boolean', 'bool'],
                'date': ['date'],
                'datetime': ['timestamp', 'timestamp without time zone']
            }
            
            # Check if PostgreSQL type is compatible with SQLite type
            type_compatible = False
            for sqlite_base_type, postgres_compatible_types in sqlite_to_postgres_type_map.items():
                if sqlite_type.startswith(sqlite_base_type) and any(postgres_type.startswith(pg_type) for pg_type in postgres_compatible_types):
                    type_compatible = True
                    break
            
            if not type_compatible:
                comparison_results['type_differences'].append({
                    'table': table,
                    'column': col_name,
                    'sqlite_type': sqlite_type,
                    'postgres_type': postgres_type
                })
    
    return comparison_results

def print_comparison_results(results):
    """Print comparison results in a readable format."""
    if not results:
        print("Unable to compare schemas due to errors.")
        return
    
    print("\n=== DATABASE SCHEMA COMPARISON RESULTS ===\n")
    
    # Print missing tables
    if results['missing_tables']:
        print("\n=== TABLES MISSING IN POSTGRESQL ===\n")
        for table in sorted(results['missing_tables']):
            print(f"- {table}")
    else:
        print("\n=== NO MISSING TABLES IN POSTGRESQL ===\n")
    
    # Print missing columns
    if results['missing_columns']:
        print("\n=== COLUMNS MISSING IN POSTGRESQL ===\n")
        missing_columns_data = []
        for col_info in sorted(results['missing_columns'], key=lambda x: (x['table'], x['column'])):
            missing_columns_data.append([col_info['table'], col_info['column'], col_info['sqlite_type']])
        
        print(tabulate(missing_columns_data, headers=['Table', 'Column', 'SQLite Type'], tablefmt='grid'))
    else:
        print("\n=== NO MISSING COLUMNS IN POSTGRESQL ===\n")
    
    # Print type differences
    if results['type_differences']:
        print("\n=== COLUMN TYPE DIFFERENCES ===\n")
        type_diff_data = []
        for diff in sorted(results['type_differences'], key=lambda x: (x['table'], x['column'])):
            type_diff_data.append([diff['table'], diff['column'], diff['sqlite_type'], diff['postgres_type']])
        
        print(tabulate(type_diff_data, headers=['Table', 'Column', 'SQLite Type', 'PostgreSQL Type'], tablefmt='grid'))
    else:
        print("\n=== NO COLUMN TYPE DIFFERENCES ===\n")

def main():
    """Main function to compare SQLite and PostgreSQL schemas."""
    # Get database paths/connection strings from environment or arguments
    sqlite_db_path = os.getenv('SQLITE_DB_PATH')
    postgres_connection_string = os.getenv('DB_CONNECTION_STRING')
    
    if len(sys.argv) > 1:
        sqlite_db_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        postgres_connection_string = sys.argv[2]
    
    if not sqlite_db_path:
        print("Error: SQLite database path not provided. Set SQLITE_DB_PATH environment variable or provide as first argument.")
        sys.exit(1)
    
    if not postgres_connection_string:
        print("Error: PostgreSQL connection string not provided. Set DB_CONNECTION_STRING environment variable or provide as second argument.")
        sys.exit(1)
    
    print(f"SQLite Database: {sqlite_db_path}")
    print(f"PostgreSQL Connection: {postgres_connection_string[:20]}...")
    
    print("\nGetting SQLite schema...")
    sqlite_schema = get_sqlite_schema(sqlite_db_path)
    
    print("Getting PostgreSQL schema...")
    postgres_schema = get_postgres_schema(postgres_connection_string)
    
    if not sqlite_schema or not postgres_schema:
        print("Failed to get schema information from one or both databases.")
        sys.exit(1)
    
    print("\nComparing schemas...")
    comparison_results = compare_schemas(sqlite_schema, postgres_schema)
    
    print_comparison_results(comparison_results)
    
    # Summary
    missing_tables_count = len(comparison_results['missing_tables'])
    missing_columns_count = len(comparison_results['missing_columns'])
    type_differences_count = len(comparison_results['type_differences'])
    
    print("\n=== SUMMARY ===\n")
    print(f"Missing Tables: {missing_tables_count}")
    print(f"Missing Columns: {missing_columns_count}")
    print(f"Type Differences: {type_differences_count}")
    
    if missing_tables_count == 0 and missing_columns_count == 0 and type_differences_count == 0:
        print("\nAll good! The schemas are compatible.")
        return 0
    else:
        print("\nWarning: Schema differences detected. This may cause application issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
