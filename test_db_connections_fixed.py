#!/usr/bin/env python3
"""
Database Connection Test Script

This script tests connections to both Render and Supabase PostgreSQL databases
to help identify connectivity issues during migration setup.

This version uses the Supavisor pooler connection which has been confirmed to work.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('.env.production', override=True)

# Get database URLs
RENDER_DB_URL = os.getenv('RENDER_DB_URL')
SUPABASE_DB_URL = os.getenv('DATABASE_URL')

def test_connection(name, url, use_ssl=False):
    """Test connection to a database"""
    print(f"\nTesting connection to {name} database...")
    print(f"URL: {url}")
    print(f"Using SSL: {use_ssl}")
    
    try:
        # Try to connect to the database
        if use_ssl:
            conn = psycopg2.connect(url, sslmode='require')
        else:
            conn = psycopg2.connect(url)
        cursor = conn.cursor()
        
        # Get database version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Connection successful!")
        print(f"Database version: {version}")
        
        # Count tables
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"Number of tables: {table_count}")
        
        # List some tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            LIMIT 5
        """)
        tables = [row[0] for row in cursor.fetchall()]
        if tables:
            print(f"Sample tables: {', '.join(tables)}")
        else:
            print("No tables found")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

def main():
    """Main function to test database connections"""
    print("Database Connection Test")
    print("=======================")
    
    # Check if URLs are set
    if not RENDER_DB_URL:
        print("ERROR: RENDER_DB_URL environment variable not set")
        sys.exit(1)
    
    if not SUPABASE_DB_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Test connections
    render_ok = test_connection("Render", RENDER_DB_URL)
    
    # Try with Supavisor pooler connection (already confirmed to work)
    print("\nTrying Supabase connection with Supavisor pooler...")
    supabase_ok = test_connection("Supabase (Pooler)", SUPABASE_DB_URL)
            
    # Summary
    print("\nConnection Test Summary:")
    print(f"- Render: {'SUCCESS' if render_ok else 'FAILED'}")
    print(f"- Supabase: {'SUCCESS' if supabase_ok else 'FAILED'}")
    
    if not render_ok and not supabase_ok:
        print("\nTroubleshooting tips:")
        print("1. Check if database URLs are correct")
        print("2. Check if your IP is whitelisted in the database firewall rules")
        print("3. Check if the database server is running and accessible")
        print("4. Try connecting using another tool like psql or a GUI client")
        sys.exit(1)
    elif not render_ok:
        print("\nMigration cannot proceed without connection to the source database (Render).")
        sys.exit(1)
    elif not supabase_ok:
        print("\nMigration cannot proceed without connection to the target database (Supabase).")
        sys.exit(1)
    else:
        print("\nAll connections successful! You can proceed with migration.")
        sys.exit(0)

if __name__ == "__main__":
    main() 