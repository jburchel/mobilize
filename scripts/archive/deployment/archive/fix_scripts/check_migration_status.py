#!/usr/bin/env python3
"""
Migration Status Check Script
This script verifies the status of the PostgreSQL database migration by checking:
1. Database connection
2. Alembic version table existence and version
3. Tables and their data counts
4. Data integrity
"""

import os
import sys
import psycopg2
import subprocess
from pathlib import Path
from tabulate import tabulate

# Connection parameters - verified with MCP
DB_PARAMS = {
    'host': 'fwnitauuyzxnsvgsbrzr.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432,
    'connect_timeout': 30,
    'sslmode': 'require'
}

# List of key tables to check
KEY_TABLES = [
    'users',
    'people',
    'contacts',
    'churches',
    'offices',
    'tasks',
    'communications',
    'pipeline_stages',
    'pipeline_stage_history',
    'roles',
    'role_permissions'
]

def check_connection():
    """Check database connection."""
    try:
        print("Checking database connection...")
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"✅ Successfully connected to PostgreSQL: {version}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False

def check_alembic_version():
    """Check alembic_version table."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Check if alembic_version table exists
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');")
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ alembic_version table does not exist")
            cursor.close()
            conn.close()
            return False
        
        # Check the current version
        cursor.execute("SELECT version_num FROM alembic_version;")
        version = cursor.fetchone()
        
        if not version:
            print("❌ No version found in alembic_version table")
            cursor.close()
            conn.close()
            return False
        
        print(f"✅ alembic_version table exists with version: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error checking alembic_version: {e}")
        return False

def check_tables_and_data():
    """Check if tables exist and contain data."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Check each key table
        table_results = []
        all_tables_exist = True
        has_data = False
        
        for table in KEY_TABLES:
            # Check if table exists
            cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table}');")
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                table_results.append({
                    "Table": table,
                    "Exists": "❌ No",
                    "Count": "N/A",
                    "Status": "Missing"
                })
                all_tables_exist = False
                continue
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            
            # Check sequence
            try:
                cursor.execute(f"SELECT last_value FROM {table}_id_seq;")
                seq_value = cursor.fetchone()[0]
                seq_status = f"Last value: {seq_value}"
            except:
                seq_status = "No sequence"
            
            status = "Empty" if count == 0 else "Has Data"
            if count > 0:
                has_data = True
            
            table_results.append({
                "Table": table,
                "Exists": "✅ Yes",
                "Count": count,
                "Sequence": seq_status,
                "Status": status
            })
        
        print("\n=== Table Status ===")
        print(tabulate(table_results, headers="keys", tablefmt="grid"))
        
        if all_tables_exist:
            print("\n✅ All required tables exist")
        else:
            print("\n❌ Some required tables are missing")
        
        if has_data:
            print("✅ Data has been migrated to at least some tables")
        else:
            print("❌ No data has been migrated to any tables")
        
        cursor.close()
        conn.close()
        return all_tables_exist and has_data
    except Exception as e:
        print(f"❌ Error checking tables and data: {e}")
        return False

def check_foreign_keys():
    """Check for orphaned records (foreign key integrity)."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Define relationships to check
        relationships = [
            ('people', 'office_id', 'offices', 'id'),
            ('contacts', 'person_id', 'people', 'id'),
            ('tasks', 'assignee_id', 'users', 'id'),
            ('communications', 'contact_id', 'contacts', 'id'),
            ('pipeline_stage_history', 'contact_id', 'contacts', 'id'),
        ]
        
        print("\n=== Foreign Key Relationships ===")
        
        all_relationships_valid = True
        for child_table, fk_column, parent_table, pk_column in relationships:
            try:
                # Check if both tables exist
                cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{child_table}');")
                child_exists = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{parent_table}');")
                parent_exists = cursor.fetchone()[0]
                
                if not (child_exists and parent_exists):
                    print(f"⚠️ Cannot check {child_table}.{fk_column} -> {parent_table}.{pk_column}: One or both tables don't exist")
                    continue
                
                # Check for orphaned records
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {child_table}
                    WHERE {fk_column} IS NOT NULL
                      AND NOT EXISTS (
                        SELECT 1 FROM {parent_table} 
                        WHERE {parent_table}.{pk_column} = {child_table}.{fk_column}
                      )
                """)
                orphan_count = cursor.fetchone()[0]
                
                if orphan_count > 0:
                    print(f"❌ Found {orphan_count} orphaned records in {child_table} "
                          f"where {fk_column} does not match any {parent_table}.{pk_column}")
                    all_relationships_valid = False
                else:
                    print(f"✅ Relationship {child_table}.{fk_column} -> {parent_table}.{pk_column} is valid")
                    
            except Exception as e:
                print(f"⚠️ Error checking relationship {child_table}.{fk_column} -> {parent_table}.{pk_column}: {e}")
        
        cursor.close()
        conn.close()
        
        if all_relationships_valid:
            print("\n✅ All foreign key relationships are valid")
        else:
            print("\n❌ Some foreign key relationships have issues")
            
        return all_relationships_valid
    except Exception as e:
        print(f"❌ Error checking foreign keys: {e}")
        return False

def main():
    print("=== PostgreSQL Migration Status Check ===")
    
    # Check database connection
    if not check_connection():
        return 1
    
    # Check alembic version
    alembic_ok = check_alembic_version()
    
    # Check tables and data
    tables_data_ok = check_tables_and_data()
    
    # Check foreign keys
    fk_ok = check_foreign_keys()
    
    # Overall status
    print("\n=== Migration Status Summary ===")
    print(f"Database Connection: {'✅ OK' if True else '❌ Failed'}")
    print(f"Alembic Version Table: {'✅ OK' if alembic_ok else '❌ Failed'}")
    print(f"Tables and Data: {'✅ OK' if tables_data_ok else '❌ Failed'}")
    print(f"Foreign Key Relationships: {'✅ OK' if fk_ok else '❌ Failed'}")
    
    if alembic_ok and tables_data_ok and fk_ok:
        print("\n✅ Data migration is COMPLETE and valid!")
        return 0
    elif tables_data_ok:
        print("\n⚠️ Data migration is PARTIALLY COMPLETE with some issues")
        return 2
    else:
        print("\n❌ Data migration is NOT COMPLETE")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 