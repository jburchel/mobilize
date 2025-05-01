#!/usr/bin/env python3
import psycopg2

# Connection parameters
db_params = {
    'host': 'aws-0-us-east-1.pooler.supabase.com',
    'database': 'postgres',
    'user': 'postgres.fwnitauuyzxnsvgsbrzr',
    'password': 'Fruitin2025',
    'port': 6543,
    'connect_timeout': 30,
    'sslmode': 'require'
}

# List of expected tables
expected_tables = [
    'users', 'people', 'contacts', 'churches', 'offices', 
    'tasks', 'communications', 'pipeline_stages', 'pipeline_stage_history',
    'roles', 'role_permissions', 'alembic_version'
]

try:
    # Connect to the database
    print("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    
    # Get all tables in the public schema
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
    tables = [table[0] for table in cursor.fetchall()]
    
    print(f"Found {len(tables)} tables in the database.")
    
    # Check for missing tables
    missing_tables = [table for table in expected_tables if table not in tables]
    
    if missing_tables:
        print("❌ Some expected tables are missing:")
        for table in missing_tables:
            print(f"  - {table}")
    else:
        print("✅ All expected tables exist in the database.")
    
    # Print all tables found
    print("\nTables in the database:")
    for table in tables:
        status = "✅" if table in expected_tables else "  "
        print(f"{status} {table}")
    
    # Check alembic_version
    if 'alembic_version' in tables:
        cursor.execute("SELECT version_num FROM alembic_version;")
        version = cursor.fetchone()
        print(f"\nalembic_version: {version[0] if version else 'No version found'}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}") 