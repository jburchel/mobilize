#!/usr/bin/env python3
"""
Script to test connection to Supabase PostgreSQL database using the exact project details
"""
import psycopg2
import sys
import time

# Connection parameters directly from Supabase project
db_params = {
    'host': 'fwnitauuyzxnsvgsbrzr.supabase.co',  # Use this hostname which does resolve
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432,
    'sslmode': 'require',
    'connect_timeout': 15  # Longer timeout
}

def test_connection():
    """Test connection to Supabase database"""
    print(f"Connecting to: {db_params['host']}")
    print(f"Database: {db_params['dbname']}")
    print(f"User: {db_params['user']}")
    print(f"Port: {db_params['port']}")
    
    try:
        conn = psycopg2.connect(**db_params)
        print("\nConnection successful!")
        
        # Run a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT current_setting('server_version');")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL version: {version}")
        
        # Check table count
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        table_count = cursor.fetchone()[0]
        print(f"Number of tables: {table_count}")
        
        # Check user count
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"Number of users: {user_count}")
        
        # Show connection string for .env.production
        conn_string = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}?sslmode={db_params['sslmode']}"
        print("\nConnection string for .env.production:")
        print(conn_string)
        
        # Close connection
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Connection error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Supabase database connection...")
    success = test_connection()
    sys.exit(0 if success else 1) 