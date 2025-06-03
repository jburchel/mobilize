#!/usr/bin/env python3
import os
import sys
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Determine the environment
ENV = os.getenv('FLASK_ENV', 'development')
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()

# Load the appropriate .env file
env_file = ROOT_DIR / f'.env.{ENV}'
if env_file.exists():
    print(f"Loading environment from {env_file}")
    load_dotenv(env_file)
else:
    # Try the regular .env file
    env_file = ROOT_DIR / '.env'
    if env_file.exists():
        print(f"Loading environment from {env_file}")
        load_dotenv(env_file)
    else:
        print("No .env file found")

def get_connection_details():
    """Print all PostgreSQL connection details from environment variables"""
    # Check for direct connection parameters
    pg_host = os.getenv('POSTGRES_HOST')
    pg_port = os.getenv('POSTGRES_PORT')
    pg_user = os.getenv('POSTGRES_USER')
    pg_pass = os.getenv('POSTGRES_PASSWORD')
    pg_db = os.getenv('POSTGRES_DB')
    
    # Check for connection string
    db_conn_string = os.getenv('DB_CONNECTION_STRING')
    
    print("---- Connection Details ----")
    if db_conn_string:
        print(f"DB_CONNECTION_STRING: {db_conn_string}")
    
    print(f"POSTGRES_HOST: {pg_host}")
    print(f"POSTGRES_PORT: {pg_port}")
    print(f"POSTGRES_USER: {pg_user}")
    print(f"POSTGRES_PASSWORD: {'*' * (len(pg_pass or '') if pg_pass else 0)}")
    print(f"POSTGRES_DB: {pg_db}")
    print("---------------------------")
    
    return pg_host, pg_port, pg_user, pg_pass, pg_db, db_conn_string

def test_connection():
    """Test connection to PostgreSQL database"""
    pg_host, pg_port, pg_user, pg_pass, pg_db, db_conn_string = get_connection_details()
    
    # Hard-coded Supabase connection parameters from migrate_data.py
    supabase_params = {
        'host': 'aws-0-us-east-1.pooler.supabase.com',
        'port': '6543',
        'user': 'postgres.fwnitauuyzxnsvgsbrzr',
        'password': 'Fruitin2025',
        'dbname': 'postgres',
        'connect_timeout': '30',
        'sslmode': 'require'
    }
    
    connection_attempts = []
    
    # Attempt 1: Try connection string if available
    if db_conn_string:
        connection_attempts.append(('Connection string', db_conn_string, None))
    
    # Attempt 2: Try individual parameters if available
    if all([pg_host, pg_port, pg_user, pg_pass, pg_db]):
        params = {
            'host': pg_host,
            'port': pg_port,
            'user': pg_user,
            'password': pg_pass,
            'dbname': pg_db
        }
        connection_attempts.append(('Environment variables', None, params))
    
    # Attempt 3: Try Supabase parameters from migrate_data.py
    connection_attempts.append(('Hard-coded Supabase settings', None, supabase_params))
    
    # Attempt 4: Try with direct db hostname
    alt_params = supabase_params.copy()
    alt_params['host'] = 'db.fwnitauuyzxnsvgsbrzr.supabase.co'
    alt_params['port'] = '5432'
    connection_attempts.append(('Direct DB hostname', None, alt_params))
    
    success = False
    
    for attempt_name, conn_string, params in connection_attempts:
        try:
            print(f"\nAttempting connection using {attempt_name}...")
            
            if conn_string:
                conn = psycopg2.connect(conn_string)
            else:
                conn = psycopg2.connect(**params)
            
            with conn.cursor() as cur:
                # Get database version
                cur.execute("SELECT version();")
                db_version = cur.fetchone()[0]
                print(f"✅ Connected successfully! PostgreSQL version: {db_version}")
                
                # Check for alembic_version table
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');")
                has_alembic = cur.fetchone()[0]
                print(f"Alembic version table exists: {has_alembic}")
                
                # Check for data in users table
                cur.execute("SELECT COUNT(*) FROM users;")
                users_count = cur.fetchone()[0]
                print(f"Number of users in database: {users_count}")
            
            conn.close()
            print(f"\n✅ SUCCESS: Connection using {attempt_name} was successful!")
            
            if attempt_name == 'Hard-coded Supabase settings':
                print("\nRecommended environment variables:")
                print("POSTGRES_HOST=aws-0-us-east-1.pooler.supabase.com")
                print("POSTGRES_PORT=6543")
                print("POSTGRES_USER=postgres.fwnitauuyzxnsvgsbrzr")
                print("POSTGRES_PASSWORD=Fruitin2025")
                print("POSTGRES_DB=postgres")
                print("\nOR as connection string:")
                print("DB_CONNECTION_STRING=postgresql://postgres.fwnitauuyzxnsvgsbrzr:Fruitin2025@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require")
            
            if attempt_name == 'Direct DB hostname':
                print("\nRecommended environment variables:")
                print("POSTGRES_HOST=db.fwnitauuyzxnsvgsbrzr.supabase.co")
                print("POSTGRES_PORT=5432")
                print("POSTGRES_USER=postgres.fwnitauuyzxnsvgsbrzr")
                print("POSTGRES_PASSWORD=Fruitin2025")
                print("POSTGRES_DB=postgres")
                print("\nOR as connection string:")
                print("DB_CONNECTION_STRING=postgresql://postgres.fwnitauuyzxnsvgsbrzr:Fruitin2025@db.fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres?sslmode=require")
            
            success = True
            break
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    if not success:
        print("\n❌ All connection attempts failed!")
        return False
        
    return True

if __name__ == "__main__":
    print("=== PostgreSQL Connection Verification ===")
    test_connection() 