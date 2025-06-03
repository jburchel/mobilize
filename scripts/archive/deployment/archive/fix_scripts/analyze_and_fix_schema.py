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

def generate_fix_script(sqlite_schema, postgres_schema):
    """Generate SQL script to fix PostgreSQL schema based on SQLite schema."""
    if not sqlite_schema or not postgres_schema:
        return None
    
    sql_commands = []
    
    # Check for missing tables
    sqlite_tables = set(sqlite_schema.keys())
    postgres_tables = set(postgres_schema.keys())
    
    missing_tables = sqlite_tables - postgres_tables
    if missing_tables:
        print(f"\nWarning: {len(missing_tables)} tables are missing in PostgreSQL. These will not be automatically created.")
        print("Missing tables: " + ", ".join(missing_tables))
    
    # Check for missing columns
    for table in sqlite_tables.intersection(postgres_tables):
        sqlite_columns = {col['name']: col for col in sqlite_schema[table]}
        postgres_columns = {col['name']: col for col in postgres_schema[table]}
        
        sqlite_column_names = set(sqlite_columns.keys())
        postgres_column_names = set(postgres_columns.keys())
        
        missing_columns = sqlite_column_names - postgres_column_names
        
        # Handle timestamp fields specially
        if 'date_created' in missing_columns and 'created_at' in postgres_column_names:
            print(f"Note: Table {table} has date_created in SQLite but created_at in PostgreSQL. Will use created_at.")
            missing_columns.remove('date_created')
        
        if 'date_modified' in missing_columns and 'updated_at' in postgres_column_names:
            print(f"Note: Table {table} has date_modified in SQLite but updated_at in PostgreSQL. Will use updated_at.")
            missing_columns.remove('date_modified')
        
        # Generate ALTER TABLE statements for missing columns
        for col_name in missing_columns:
            sqlite_type = sqlite_columns[col_name]['type'].lower()
            postgres_type = map_sqlite_to_postgres_type(sqlite_type)
            
            # Skip id columns (they're usually handled by the ORM)
            if col_name == 'id' and sqlite_columns[col_name]['pk'] == 1:
                continue
                
            sql_commands.append(f"""-- Adding {col_name} to {table}
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = '{table}' AND column_name = '{col_name}') THEN
                    ALTER TABLE {table} ADD COLUMN {col_name} {postgres_type};
                    RAISE NOTICE 'Added column {col_name} to {table}';
                END IF;
            END $$;""")
    
    return "\n\n".join(sql_commands)

def map_sqlite_to_postgres_type(sqlite_type):
    """Map SQLite data types to PostgreSQL data types."""
    sqlite_type = sqlite_type.lower()
    
    # Common type mappings
    type_map = {
        'integer': 'INTEGER',
        'int': 'INTEGER',
        'tinyint': 'SMALLINT',
        'smallint': 'SMALLINT',
        'mediumint': 'INTEGER',
        'bigint': 'BIGINT',
        'unsigned big int': 'BIGINT',
        'text': 'TEXT',
        'character': 'CHARACTER',
        'varchar': 'VARCHAR',
        'varying character': 'VARCHAR',
        'nchar': 'CHAR',
        'native character': 'CHAR',
        'nvarchar': 'VARCHAR',
        'clob': 'TEXT',
        'real': 'REAL',
        'double': 'DOUBLE PRECISION',
        'double precision': 'DOUBLE PRECISION',
        'float': 'REAL',
        'numeric': 'NUMERIC',
        'decimal': 'DECIMAL',
        'boolean': 'BOOLEAN',
        'date': 'DATE',
        'datetime': 'TIMESTAMP WITHOUT TIME ZONE',
        'timestamp': 'TIMESTAMP WITHOUT TIME ZONE',
        'blob': 'BYTEA',
        'json': 'JSONB'
    }
    
    # Handle types with length specifications like VARCHAR(100)
    for base_type in ['varchar', 'character', 'char', 'nchar', 'nvarchar']:
        if sqlite_type.startswith(base_type + '('):
            length = sqlite_type[sqlite_type.find('(')+1:sqlite_type.find(')')]
            return f"VARCHAR({length})"
    
    # Default mapping
    for base_type, pg_type in type_map.items():
        if sqlite_type.startswith(base_type):
            return pg_type
    
    # If no match found, default to TEXT
    print(f"Warning: Unknown SQLite type '{sqlite_type}', defaulting to TEXT")
    return 'TEXT'

def fix_postgres_schema(connection_string, sql_script):
    """Execute SQL script to fix PostgreSQL schema."""
    if not sql_script:
        print("No SQL script to execute.")
        return False
    
    try:
        conn = psycopg2.connect(connection_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Split the script into individual statements
        statements = sql_script.split(';\n\n')
        
        for statement in statements:
            if statement.strip():
                print(f"Executing:\n{statement}")
                cursor.execute(statement)
                print("Statement executed successfully.")
        
        cursor.close()
        conn.close()
        print("Schema update completed successfully.")
        return True
    except Exception as e:
        print(f"Error executing SQL script: {str(e)}")
        return False

def main():
    """Main function to analyze and fix database schemas."""
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
    
    print("\nGenerating SQL fix script...")
    sql_script = generate_fix_script(sqlite_schema, postgres_schema)
    
    if not sql_script:
        print("No schema differences to fix.")
        return 0
    
    # Save the SQL script to a file
    script_path = 'fix_postgres_schema.sql'
    with open(script_path, 'w') as f:
        f.write(sql_script)
    print(f"SQL script saved to {script_path}")
    
    # Automatically execute the script
    print("\nExecuting SQL script to fix the PostgreSQL schema...")
    success = fix_postgres_schema(postgres_connection_string, sql_script)
    if success:
        print("PostgreSQL schema has been updated successfully.")
        return 0
    else:
        print("Failed to update PostgreSQL schema.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
