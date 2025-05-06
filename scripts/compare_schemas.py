#!/usr/bin/env python3
"""
Schema comparison utility for Mobilize CRM

This script compares database schemas between development and production environments.
It connects to both databases and compares tables, columns, and their types.
"""

import os
import sys
import logging
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import json

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('schema-compare')

# Get the application root directory
ROOT_DIR = Path(__file__).parent.parent.absolute()

# Load environment variables
dev_env_path = ROOT_DIR / '.env.development'
load_dotenv(dev_env_path)
DEV_DB_URI = os.getenv('DB_CONNECTION_STRING')

prod_env_path = ROOT_DIR / '.env.production'
load_dotenv(prod_env_path, override=True)
PROD_DB_URI = os.getenv('DB_CONNECTION_STRING')

# Restore environment variables
load_dotenv(dev_env_path, override=True)

def get_schema_info(connection_string, env_name):
    """Get schema information from a database"""
    try:
        logger.info(f"Connecting to {env_name} database...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(tables)} tables in {env_name} database")
        
        schema_info = {}
        for table in tables:
            # Get columns for each table
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            columns = [{
                'name': row[0],
                'type': row[1],
                'max_length': row[2],
                'nullable': row[3]
            } for row in cursor.fetchall()]
            
            schema_info[table] = columns
        
        cursor.close()
        conn.close()
        return schema_info
    except Exception as e:
        logger.error(f"Error getting schema info from {env_name} database: {str(e)}")
        return None

def compare_schemas(dev_schema, prod_schema):
    """Compare schemas between development and production"""
    if not dev_schema or not prod_schema:
        logger.error("Cannot compare schemas - one or both schemas are missing")
        return False
    
    # Compare tables
    dev_tables = set(dev_schema.keys())
    prod_tables = set(prod_schema.keys())
    
    # Tables in dev but not in prod
    dev_only_tables = dev_tables - prod_tables
    if dev_only_tables:
        logger.warning(f"Tables in development but not in production: {', '.join(dev_only_tables)}")
    
    # Tables in prod but not in dev
    prod_only_tables = prod_tables - dev_tables
    if prod_only_tables:
        logger.warning(f"Tables in production but not in development: {', '.join(prod_only_tables)}")
    
    # Common tables
    common_tables = dev_tables.intersection(prod_tables)
    logger.info(f"Found {len(common_tables)} common tables")
    
    # Compare columns for common tables
    all_match = True
    for table in common_tables:
        dev_columns = {col['name']: col for col in dev_schema[table]}
        prod_columns = {col['name']: col for col in prod_schema[table]}
        
        # Columns in dev but not in prod
        dev_only_columns = set(dev_columns.keys()) - set(prod_columns.keys())
        if dev_only_columns:
            logger.warning(f"Table '{table}' has columns in development but not in production: {', '.join(dev_only_columns)}")
            all_match = False
        
        # Columns in prod but not in dev
        prod_only_columns = set(prod_columns.keys()) - set(dev_columns.keys())
        if prod_only_columns:
            logger.warning(f"Table '{table}' has columns in production but not in development: {', '.join(prod_only_columns)}")
            all_match = False
        
        # Common columns
        common_columns = set(dev_columns.keys()).intersection(set(prod_columns.keys()))
        
        # Compare column types
        for col_name in common_columns:
            dev_col = dev_columns[col_name]
            prod_col = prod_columns[col_name]
            
            if dev_col['type'] != prod_col['type']:
                logger.warning(f"Column '{table}.{col_name}' has different types: dev={dev_col['type']}, prod={prod_col['type']}")
                all_match = False
            
            # Compare nullability
            if dev_col['nullable'] != prod_col['nullable']:
                logger.warning(f"Column '{table}.{col_name}' has different nullability: dev={dev_col['nullable']}, prod={prod_col['nullable']}")
                all_match = False
    
    return all_match

def main():
    # Get schema info
    dev_schema = get_schema_info(DEV_DB_URI, "development")
    prod_schema = get_schema_info(PROD_DB_URI, "production")
    
    # Compare schemas
    schemas_match = compare_schemas(dev_schema, prod_schema)
    
    if schemas_match:
        logger.info("✅ Schemas match between development and production!")
    else:
        logger.warning("❌ Schemas do not match between development and production")
    
    # Save schema info to files for reference
    if dev_schema:
        with open(ROOT_DIR / 'dev_schema.json', 'w') as f:
            json.dump(dev_schema, f, indent=2)
        logger.info("Development schema saved to dev_schema.json")
    
    if prod_schema:
        with open(ROOT_DIR / 'prod_schema.json', 'w') as f:
            json.dump(prod_schema, f, indent=2)
        logger.info("Production schema saved to prod_schema.json")

if __name__ == '__main__':
    main()
