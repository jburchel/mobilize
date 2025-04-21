#!/usr/bin/env python3
"""
PostgreSQL Migration Test Script (Final Version)

This script tests database connectivity and migration SQL against PostgreSQL
without actually applying the migrations. It extracts SQL statements from 
migration files and validates database structure.
"""

import os
import sys
import re
import glob
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='[%(asctime)s] %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("pg_migration_test")

# Load environment variables
load_dotenv()
load_dotenv('.env.production', override=True)

# Migration directory
migrations_dir = os.path.join(os.getcwd(), 'migrations', 'versions')

def find_latest_migration():
    """Find the latest migration file in the versions directory"""
    logger.info(f"Looking for migration files in {migrations_dir}")
    
    # Get all .py files in migrations/versions directory
    migration_files = glob.glob(os.path.join(migrations_dir, '*.py'))
    
    if not migration_files:
        logger.error("No migration files found in migrations/versions directory")
        return None
    
    # Sort by filename (Alembic names migrations with timestamps)
    migration_files.sort()
    latest_migration = os.path.basename(migration_files[-1])
    
    logger.info(f"Latest migration file: {latest_migration}")
    return latest_migration

def extract_alembic_operations(file_path):
    """Extract Alembic operation calls from a migration file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Look for op.* operations
    operations = []
    
    # Pattern for common Alembic operations
    patterns = {
        'add_column': r'op\.add_column\([\'"](.+?)[\'"]\s*,\s*(.+?)\s*\)',
        'drop_column': r'op\.drop_column\([\'"](.+?)[\'"]\s*,\s*[\'"](.+?)[\'"]\s*\)',
        'create_table': r'op\.create_table\([\'"](.+?)[\'"]\s*,(.+?)\s*\)',
        'drop_table': r'op\.drop_table\([\'"](.+?)[\'"]\s*\)',
        'create_index': r'op\.create_index\([\'"](.+?)[\'"]\s*,\s*[\'"](.+?)[\'"]\s*,(.+?)\s*\)',
        'drop_index': r'op\.drop_index\([\'"](.+?)[\'"]\s*,\s*[\'"](.+?)[\'"]\s*\)',
        'alter_column': r'op\.alter_column\([\'"](.+?)[\'"]\s*,\s*[\'"](.+?)[\'"]\s*,(.+?)\s*\)',
        'create_foreign_key': r'op\.create_foreign_key\([\'"](.+?)[\'"]\s*,\s*[\'"](.+?)[\'"]\s*,(.+?)\s*\)',
        'execute': r'op\.execute\(\s*[\'"](.+?)[\'"]\s*\)'
    }
    
    for op_type, pattern in patterns.items():
        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            if isinstance(match, tuple):
                operations.append(f"{op_type}: {', '.join(str(m) for m in match)}")
            else:
                operations.append(f"{op_type}: {match}")
    
    return operations

def extract_raw_sql(file_path):
    """Extract raw SQL statements from a migration file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    sql_statements = []
    
    # Different patterns for SQL extraction
    patterns = [
        # session.execute(text("SQL"))
        r'session\.execute\(\s*text\(\s*[\'"](.+?)[\'"]\s*\)\s*\)',
        # op.execute("SQL")
        r'op\.execute\(\s*[\'"](.+?)[\'"]\s*\)',
        # conn.execute(text("SQL"))
        r'conn\.execute\(\s*text\(\s*[\'"](.+?)[\'"]\s*\)\s*\)',
        # engine.execute("SQL")
        r'engine\.execute\(\s*[\'"](.+?)[\'"]\s*\)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        sql_statements.extend(matches)
    
    return sql_statements

def main():
    """Main function to test PostgreSQL migrations"""
    logger.info("Starting PostgreSQL Migration Test (Final Version)")
    
    # Determine which migration file to use
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]
        if not os.path.exists(os.path.join(migrations_dir, migration_file)):
            logger.error(f"Migration file not found: {migration_file}")
            return
    else:
        migration_file = find_latest_migration()
        if not migration_file:
            logger.error("No migration file found or specified")
            return
    
    # Full path to the migration file
    file_path = os.path.join(migrations_dir, migration_file)
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 
        "postgresql://postgres.fwnitauuyzxnsvgsbrzr:RV4QOygx0LpqOjzx@aws-0-us-east-1.pooler.supabase.com:5432/postgres")
    
    logger.info(f"Using database URL: {db_url}")
    
    # Extract operations and SQL from the migration file
    alembic_ops = extract_alembic_operations(file_path)
    raw_sql = extract_raw_sql(file_path)
    
    logger.info(f"Found {len(alembic_ops)} Alembic operations in the migration file")
    logger.info(f"Found {len(raw_sql)} raw SQL statements in the migration file")
    
    # Create a timestamp for the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sql_output_file = f"migration_sql_{timestamp}.sql"
    
    # Build the SQL commands output
    all_sql = "-- Migration SQL Preview\n"
    all_sql += f"-- Generated from {migration_file} on {datetime.now()}\n\n"
    
    # Add Alembic operations
    if alembic_ops:
        all_sql += "-- Alembic Operations:\n"
        for i, op in enumerate(alembic_ops, 1):
            all_sql += f"-- {i}. {op}\n"
        all_sql += "\n"
    
    # Add raw SQL statements
    if raw_sql:
        all_sql += "-- Raw SQL Statements:\n"
        for i, sql in enumerate(raw_sql, 1):
            all_sql += f"-- {i}. {sql}\n"
            # Also add executable SQL
            all_sql += f"{sql};\n\n"
    
    # Write to file
    with open(sql_output_file, 'w') as f:
        f.write(all_sql)
    
    logger.info(f"SQL commands written to {sql_output_file}")
    
    # Display preview
    logger.info("\n--- SQL COMMANDS PREVIEW ---\n")
    sql_lines = all_sql.split('\n')
    preview_lines = sql_lines[:20]
    logger.info('\n'.join(preview_lines))
    
    if len(sql_lines) > 20:
        logger.info(f"... and {len(sql_lines) - 20} more lines")
    
    # Test connection
    try:
        engine = create_engine(db_url, echo=False)
        
        with engine.connect() as conn:
            logger.info("Successfully connected to PostgreSQL database")
            
            # Test basic SQL query
            result = conn.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            logger.info(f"Connected to database: {db_info[0]} as user: {db_info[1]}")
            
            # Get database schema information
            inspector = inspect(engine)
            
            # Get table names
            tables = inspector.get_table_names()
            logger.info(f"Found {len(tables)} tables in database: {', '.join(tables[:5])}...")
            
            # Get column info for tables mentioned in operations
            referenced_tables = set()
            
            # Extract table names from operations
            for op in alembic_ops:
                # Simple extraction for demonstration
                parts = op.split(":")
                if len(parts) > 1:
                    table_part = parts[1].strip()
                    table_name = table_part.split(",")[0].strip().strip("'\"")
                    if table_name in tables:
                        referenced_tables.add(table_name)
            
            # Check raw SQL for table references
            for sql in raw_sql:
                # Simple regex to find table names after UPDATE, INSERT, ALTER, etc.
                table_matches = re.findall(r'(UPDATE|INSERT\s+INTO|ALTER\s+TABLE|CREATE\s+TABLE|DROP\s+TABLE)\s+([a-z0-9_]+)', 
                                         sql, re.IGNORECASE)
                for _, table in table_matches:
                    if table in tables:
                        referenced_tables.add(table)
            
            # Get column details for referenced tables
            logger.info("\n--- REFERENCED TABLES STRUCTURE ---\n")
            
            for table in referenced_tables:
                columns = inspector.get_columns(table)
                logger.info(f"Table '{table}' structure:")
                for col in columns:
                    logger.info(f"  - {col['name']}: {col['type']}")
                
                # Get foreign keys
                fks = inspector.get_foreign_keys(table)
                if fks:
                    logger.info(f"  Foreign Keys:")
                    for fk in fks:
                        logger.info(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
                
                logger.info("")
                
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("PostgreSQL migration test completed")

if __name__ == "__main__":
    main() 