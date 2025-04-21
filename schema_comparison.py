#!/usr/bin/env python3
"""
Schema Comparison Tool for PostgreSQL Databases

This script compares the schema differences between two PostgreSQL databases
(Render and Supabase) to help identify potential mapping issues for migration.

Usage:
    python schema_comparison.py [--table TABLE_NAME]

Arguments:
    --table: Optional specific table to compare (otherwise compares all tables)

Output:
    Generates a schema_diff_report.txt file with comparison results
"""

import os
import sys
import argparse
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables
load_dotenv()
load_dotenv('.env.production', override=True)

# Configuration
RENDER_DB_URL = os.getenv('RENDER_DB_URL')
SUPABASE_DB_URL = os.getenv('DATABASE_URL')

@contextmanager
def connect_db(connection_string, db_name):
    """Context manager for database connection"""
    if not connection_string:
        raise ValueError(f"{db_name} database URL environment variable not set")
        
    conn = psycopg2.connect(connection_string)
    try:
        yield conn
    finally:
        conn.close()

def get_tables(conn):
    """Get all table names in the database"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_table_schema(conn, table_name):
    """Get detailed column information for a table"""
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Get columns
    cursor.execute("""
        SELECT 
            column_name, 
            data_type, 
            character_maximum_length,
            is_nullable,
            column_default,
            ordinal_position
        FROM information_schema.columns
        WHERE table_name = %s
        AND table_schema = 'public'
        ORDER BY ordinal_position
    """, (table_name,))
    
    columns = cursor.fetchall()
    column_details = {}
    
    for col in columns:
        column_details[col['column_name']] = {
            'data_type': col['data_type'],
            'length': col['character_maximum_length'],
            'nullable': col['is_nullable'] == 'YES',
            'default': col['column_default'],
            'position': col['ordinal_position']
        }
    
    # Get primary key
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
    
    # Get foreign keys
    cursor.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s
        ORDER BY kcu.column_name
    """, (table_name,))
    
    foreign_keys = []
    for row in cursor.fetchall():
        foreign_keys.append({
            'column': row['column_name'],
            'references_table': row['foreign_table_name'],
            'references_column': row['foreign_column_name']
        })
    
    # Get indexes
    cursor.execute("""
        SELECT
            i.relname AS index_name,
            array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) AS column_names,
            ix.indisunique AS is_unique
        FROM
            pg_index ix
        JOIN
            pg_class i ON i.oid = ix.indexrelid
        JOIN
            pg_class t ON t.oid = ix.indrelid
        JOIN
            pg_attribute a ON a.attrelid = t.oid
        WHERE
            t.relname = %s
            AND a.attnum = ANY(ix.indkey)
            AND t.relkind = 'r'
        GROUP BY
            i.relname, ix.indisunique
        ORDER BY
            i.relname
    """, (table_name,))
    
    indexes = []
    for row in cursor.fetchall():
        indexes.append({
            'name': row['index_name'],
            'columns': row['column_names'],
            'unique': row['is_unique']
        })
    
    cursor.close()
    
    return {
        'columns': column_details,
        'primary_keys': primary_keys,
        'foreign_keys': foreign_keys,
        'indexes': indexes
    }

def compare_schemas(render_schema, supabase_schema):
    """Compare schema differences between databases"""
    comparison_result = {
        'columns_only_in_render': [],
        'columns_only_in_supabase': [],
        'column_type_differences': [],
        'column_nullable_differences': [],
        'pk_differences': False,
        'fk_differences': [],
        'render_pk': render_schema['primary_keys'],
        'supabase_pk': supabase_schema['primary_keys'],
        'render_fk': render_schema['foreign_keys'],
        'supabase_fk': supabase_schema['foreign_keys']
    }
    
    # Compare columns
    render_columns = set(render_schema['columns'].keys())
    supabase_columns = set(supabase_schema['columns'].keys())
    
    comparison_result['columns_only_in_render'] = list(render_columns - supabase_columns)
    comparison_result['columns_only_in_supabase'] = list(supabase_columns - render_columns)
    
    # Compare column types and nullable status
    for col_name in render_columns.intersection(supabase_columns):
        render_col = render_schema['columns'][col_name]
        supabase_col = supabase_schema['columns'][col_name]
        
        # Check type differences
        render_type = render_col['data_type']
        supabase_type = supabase_col['data_type']
        
        if render_type != supabase_type:
            comparison_result['column_type_differences'].append({
                'column': col_name,
                'render_type': f"{render_type}" + (f"({render_col['length']})" if render_col['length'] else ""),
                'supabase_type': f"{supabase_type}" + (f"({supabase_col['length']})" if supabase_col['length'] else "")
            })
        
        # Check nullable differences
        if render_col['nullable'] != supabase_col['nullable']:
            comparison_result['column_nullable_differences'].append({
                'column': col_name,
                'render_nullable': render_col['nullable'],
                'supabase_nullable': supabase_col['nullable']
            })
    
    # Compare primary keys
    if set(render_schema['primary_keys']) != set(supabase_schema['primary_keys']):
        comparison_result['pk_differences'] = True
    
    # Compare foreign keys
    render_fks = {f"{fk['column']}_refs_{fk['references_table']}.{fk['references_column']}": fk for fk in render_schema['foreign_keys']}
    supabase_fks = {f"{fk['column']}_refs_{fk['references_table']}.{fk['references_column']}": fk for fk in supabase_schema['foreign_keys']}
    
    for fk_key in set(render_fks.keys()) - set(supabase_fks.keys()):
        comparison_result['fk_differences'].append({
            'type': 'missing_in_supabase',
            'details': render_fks[fk_key]
        })
    
    for fk_key in set(supabase_fks.keys()) - set(render_fks.keys()):
        comparison_result['fk_differences'].append({
            'type': 'missing_in_render',
            'details': supabase_fks[fk_key]
        })
    
    return comparison_result

def generate_column_mappings(comparison_results):
    """Generate potential column mappings based on comparison results"""
    mappings = {}
    
    for table, result in comparison_results.items():
        table_mappings = {}
        
        # Look for similar column names in both databases
        for render_col in result['columns_only_in_render']:
            for supabase_col in result['columns_only_in_supabase']:
                # Simple similarity check - if one is contained in the other
                if (render_col in supabase_col or supabase_col in render_col):
                    table_mappings[render_col] = supabase_col
                    break
        
        if table_mappings:
            mappings[table] = table_mappings
    
    return mappings

def main():
    parser = argparse.ArgumentParser(description='Compare schema differences between Render and Supabase databases')
    parser.add_argument('--table', help='Compare specific table only')
    args = parser.parse_args()
    
    if not RENDER_DB_URL:
        print("ERROR: RENDER_DB_URL environment variable not set")
        print("Please add RENDER_DB_URL to your .env.production file")
        sys.exit(1)
    
    if not SUPABASE_DB_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please add DATABASE_URL to your .env.production file")
        sys.exit(1)
    
    print("Starting schema comparison...")
    
    try:
        with connect_db(RENDER_DB_URL, "Render") as render_conn, connect_db(SUPABASE_DB_URL, "Supabase") as supabase_conn:
            # Get tables to compare
            render_tables = get_tables(render_conn)
            supabase_tables = get_tables(supabase_conn)
            
            tables_to_compare = []
            if args.table:
                if args.table in render_tables and args.table in supabase_tables:
                    tables_to_compare = [args.table]
                else:
                    if args.table not in render_tables:
                        print(f"Table '{args.table}' not found in Render database")
                    if args.table not in supabase_tables:
                        print(f"Table '{args.table}' not found in Supabase database")
                    sys.exit(1)
            else:
                # Find tables present in both databases
                tables_to_compare = sorted(list(set(render_tables) & set(supabase_tables)))
            
            # Tables only in one database
            tables_only_in_render = sorted(list(set(render_tables) - set(supabase_tables)))
            tables_only_in_supabase = sorted(list(set(supabase_tables) - set(render_tables)))
            
            comparison_results = {}
            
            # Compare each table
            for table in tables_to_compare:
                print(f"Comparing table: {table}")
                render_schema = get_table_schema(render_conn, table)
                supabase_schema = get_table_schema(supabase_conn, table)
                comparison_results[table] = compare_schemas(render_schema, supabase_schema)
            
            # Generate potential column mappings
            column_mappings = generate_column_mappings(comparison_results)
            
            # Generate report
            with open('schema_diff_report.txt', 'w') as report:
                report.write("Schema Comparison Report\n")
                report.write("=======================\n\n")
                
                report.write("Tables only in Render:\n")
                for table in tables_only_in_render:
                    report.write(f"  - {table}\n")
                report.write("\n")
                
                report.write("Tables only in Supabase:\n")
                for table in tables_only_in_supabase:
                    report.write(f"  - {table}\n")
                report.write("\n")
                
                report.write("Table Differences:\n")
                report.write("=================\n\n")
                
                for table in tables_to_compare:
                    result = comparison_results[table]
                    
                    if (not result['columns_only_in_render'] and 
                        not result['columns_only_in_supabase'] and 
                        not result['column_type_differences'] and 
                        not result['column_nullable_differences'] and 
                        not result['pk_differences'] and 
                        not result['fk_differences']):
                        report.write(f"Table '{table}': No differences found\n\n")
                        continue
                    
                    report.write(f"Table '{table}':\n")
                    
                    if result['columns_only_in_render']:
                        report.write("  Columns only in Render:\n")
                        for col in result['columns_only_in_render']:
                            render_col = render_schema['columns'][col]
                            col_type = f"{render_col['data_type']}" + (f"({render_col['length']})" if render_col['length'] else "")
                            report.write(f"    - {col} ({col_type})\n")
                    
                    if result['columns_only_in_supabase']:
                        report.write("  Columns only in Supabase:\n")
                        for col in result['columns_only_in_supabase']:
                            supabase_col = supabase_schema['columns'][col]
                            col_type = f"{supabase_col['data_type']}" + (f"({supabase_col['length']})" if supabase_col['length'] else "")
                            report.write(f"    - {col} ({col_type})\n")
                    
                    if result['column_type_differences']:
                        report.write("  Column type differences:\n")
                        for diff in result['column_type_differences']:
                            report.write(f"    - {diff['column']}: {diff['render_type']} (Render) vs {diff['supabase_type']} (Supabase)\n")
                    
                    if result['column_nullable_differences']:
                        report.write("  Column nullable differences:\n")
                        for diff in result['column_nullable_differences']:
                            report.write(f"    - {diff['column']}: {'NULL' if diff['render_nullable'] else 'NOT NULL'} (Render) vs {'NULL' if diff['supabase_nullable'] else 'NOT NULL'} (Supabase)\n")
                    
                    if result['pk_differences']:
                        report.write("  Primary key differences:\n")
                        render_pks = ", ".join(result['render_pk']) if result['render_pk'] else "None"
                        supabase_pks = ", ".join(result['supabase_pk']) if result['supabase_pk'] else "None"
                        report.write(f"    - Render: {render_pks}\n")
                        report.write(f"    - Supabase: {supabase_pks}\n")
                    
                    if result['fk_differences']:
                        report.write("  Foreign key differences:\n")
                        for diff in result['fk_differences']:
                            if diff['type'] == 'missing_in_supabase':
                                fk = diff['details']
                                report.write(f"    - Missing in Supabase: {fk['column']} references {fk['references_table']}.{fk['references_column']}\n")
                            else:
                                fk = diff['details']
                                report.write(f"    - Missing in Render: {fk['column']} references {fk['references_table']}.{fk['references_column']}\n")
                    
                    report.write("\n")
                
                # Write suggested column mappings
                if column_mappings:
                    report.write("\nSuggested Column Mappings:\n")
                    report.write("=========================\n\n")
                    report.write("Add these to COLUMN_MAPPINGS in migrate_render_to_supabase.py:\n\n")
                    report.write("COLUMN_MAPPINGS = {\n")
                    
                    for table, mappings in column_mappings.items():
                        if mappings:
                            report.write(f"    '{table}': {{\n")
                            for render_col, supabase_col in mappings.items():
                                report.write(f"        '{render_col}': '{supabase_col}',\n")
                            report.write("    },\n")
                    
                    report.write("}\n")
            
            print(f"\nSchema comparison completed. See 'schema_diff_report.txt' for details.")
            print(f"Found differences in {sum(1 for result in comparison_results.values() if any(len(result[key]) > 0 for key in result if key not in ['render_pk', 'supabase_pk', 'render_fk', 'supabase_fk']) or result['pk_differences'])} tables.")
            
            if column_mappings:
                print(f"Generated suggested column mappings for {len(column_mappings)} tables.")
    
    except Exception as e:
        print(f"Error during schema comparison: {e}")
        raise

if __name__ == "__main__":
    main() 