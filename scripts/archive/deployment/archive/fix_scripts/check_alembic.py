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

try:
    # Connect to the database
    print("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    
    # Check if alembic_version table exists
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');")
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        print("✅ alembic_version table exists.")
        cursor.execute("SELECT version_num FROM alembic_version;")
        version = cursor.fetchone()
        print(f"Current version: {version[0] if version else 'No version found'}")
    else:
        print("❌ alembic_version table does not exist! Migration tracking might be compromised.")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}") 