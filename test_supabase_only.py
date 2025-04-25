#!/usr/bin/env python3
"""
Supabase Database Connection Test Script

This script tests connection to Supabase PostgreSQL database
using the Supavisor connection pooler format.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('.env.production', override=True)

# Get database URL
SUPABASE_DB_URL = os.getenv('DATABASE_URL', 
    "postgresql://postgres.fwnitauuyzxnsvgsbrzr:RV4QOygx0LpqOjzx@aws-0-us-east-1.pooler.supabase.com:5432/postgres")

def test_connection(name, url):
    """Test connection to a database"""
    print(f"\nTesting connection to {name} database...")
    print(f"URL: {url}")
    
    try:
        # Try to connect to the database
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
    """Main function to test database connection"""
    print("Supabase Database Connection Test")
    print("=================================")
    
    # Check if URL is set
    if not SUPABASE_DB_URL:
        print("ERROR: DATABASE_URL environment variable not set, using hardcoded value")
    
    # Try with Supavisor pooler connection
    print("\nTrying Supabase connection with Supavisor pooler...")
    supabase_ok = test_connection("Supabase (Pooler)", SUPABASE_DB_URL)
            
    # Summary
    print("\nConnection Test Summary:")
    print(f"- Supabase: {'SUCCESS' if supabase_ok else 'FAILED'}")
    
    if not supabase_ok:
        print("\nTroubleshooting tips:")
        print("1. Check if database URL is correct")
        print("2. Check if your IP is whitelisted in the database firewall rules")
        print("3. Check if the database server is running and accessible")
        print("4. Try connecting using another tool like psql or a GUI client")
        sys.exit(1)
    else:
        print("\nConnection successful! You can proceed with database operations.")
        sys.exit(0)

if __name__ == "__main__":
    main() 