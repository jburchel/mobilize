#!/usr/bin/env python3
"""
Database Connection Test Script

This script tests connections to both Render and Supabase PostgreSQL databases
to help identify connectivity issues during migration setup.
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
        print(f"Sample tables: {', '.join(tables)}")
        
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
    
    # Try standard Supabase URL format
    supabase_ok = test_connection("Supabase", SUPABASE_DB_URL)
    
    # If that fails, try alternative Supabase URL format
    if not supabase_ok:
        print("\nTrying alternative Supabase URL format...")
        # Extract credentials from the original URL
        parts = SUPABASE_DB_URL.split('@')
        if len(parts) >= 2:
            credentials = parts[0]
            project_id = 'fwnitauuyzxnsvgsbrzr'  # Extracted from environment file
            alt_url = f"{credentials}@{project_id}.supabase.co:5432/postgres"
            supabase_ok = test_connection("Supabase (alt)", alt_url)
    
    # If still not successful, try with SSL
    if not supabase_ok:
        print("\nTrying Supabase connection with SSL enabled...")
        supabase_ok = test_connection("Supabase with SSL", SUPABASE_DB_URL, use_ssl=True)
        
        if not supabase_ok:
            print("\nTrying alternative Supabase URL with SSL enabled...")
            parts = SUPABASE_DB_URL.split('@')
            if len(parts) >= 2:
                credentials = parts[0]
                project_id = 'fwnitauuyzxnsvgsbrzr'
                alt_url = f"{credentials}@{project_id}.supabase.co:5432/postgres"
                supabase_ok = test_connection("Supabase (alt) with SSL", alt_url, use_ssl=True)
                
                # If that works, suggest updating the .env file
                if supabase_ok:
                    print("\nNOTE: The alternative Supabase URL format with SSL worked. Consider updating your .env.production file.")
            
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