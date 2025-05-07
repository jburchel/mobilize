#!/usr/bin/env python3
"""
Schema synchronization utility for Mobilize CRM

This script helps synchronize database schema between development and production environments.
It extracts the schema from the production Supabase database and applies it to the local development database.
"""

import os
import sys
import argparse
import logging
import subprocess
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('schema-sync')

# Get the application root directory
ROOT_DIR = Path(__file__).parent.parent.absolute()

# Load development environment variables first
load_dotenv(ROOT_DIR / '.env.development')

# Store development connection string
DEV_DB_URI = os.getenv('DB_CONNECTION_STRING')
if not DEV_DB_URI:
    logger.error("Development DB_CONNECTION_STRING not found in .env.development")
    sys.exit(1)

# Now load production environment variables with override=False to preserve DEV_DB_URI
load_dotenv(ROOT_DIR / '.env.production', override=False)

# Get production connection string from a separate environment variable
os.environ['PROD_DB_CONNECTION_STRING'] = os.getenv('DB_CONNECTION_STRING')

# Now restore the development connection string that was overridden
os.environ['DB_CONNECTION_STRING'] = DEV_DB_URI

# Production database connection parameters
PROD_DB_URI = os.environ.get('PROD_DB_CONNECTION_STRING')
if not PROD_DB_URI:
    logger.error("Production DB_CONNECTION_STRING not found in .env.production")
    sys.exit(1)

def extract_schema_from_production():
    """Extract schema from production database"""
    try:
        logger.info("Extracting schema from production database...")
        # Print the connection string for debugging (without password)
        safe_uri = PROD_DB_URI.replace(PROD_DB_URI.split(':')[2].split('@')[0], '****')
        logger.info(f"Production DB URI: {safe_uri}")
        
        # Parse connection string for Supabase format
        # Format: postgresql://user:password@host:port/dbname?sslmode=require
        
        # First split by ://
        if '://' not in PROD_DB_URI:
            logger.error("Invalid connection string format")
            return None
            
        protocol, rest = PROD_DB_URI.split('://', 1)
        
        # Split user:password from host:port/dbname
        if '@' not in rest:
            logger.error("Invalid connection string format - missing @")
            return None
            
        user_pass, host_port_db = rest.split('@', 1)
        
        # Get user and password
        if ':' not in user_pass:
            logger.error("Invalid connection string format - missing : in credentials")
            return None
            
        user, password = user_pass.split(':', 1)
        
        # Get host, port, and dbname
        if '/' not in host_port_db:
            logger.error("Invalid connection string format - missing / for dbname")
            return None
            
        host_port, dbname_params = host_port_db.split('/', 1)
        
        # Get host and port
        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            host = host_port
            port = '5432'
            
        # Get dbname without parameters
        if '?' in dbname_params:
            dbname = dbname_params.split('?', 1)[0]
        else:
            dbname = dbname_params
        
        # Use pg_dump to extract schema
        schema_file = ROOT_DIR / 'schema.sql'
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', dbname,
            '--schema-only',
            '-f', str(schema_file)
        ]
        
        # Set PGPASSWORD environment variable for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        logger.info(f"Running: {' '.join(cmd)}")
        process = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error extracting schema: {process.stderr}")
            return None
        
        logger.info(f"Schema extracted to {schema_file}")
        return schema_file
    except Exception as e:
        logger.error(f"Error extracting schema: {str(e)}")
        return None

def apply_schema_to_development(schema_file):
    """Apply schema to development database"""
    try:
        logger.info("Applying schema to development database...")
        # Parse connection string to get components
        parts = DEV_DB_URI.split('://', 1)[1].split('@')
        user_pass = parts[0].split(':')
        host_port_db = parts[1].split('/')
        
        user = user_pass[0]
        password = user_pass[1]
        host_port = host_port_db[0].split(':')
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else '5432'
        dbname = host_port_db[1]
        
        # Use psql to apply schema
        cmd = [
            'psql',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', dbname,
            '-f', str(schema_file)
        ]
        
        # Set PGPASSWORD environment variable for psql
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        logger.info(f"Running: {' '.join(cmd)}")
        process = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error applying schema: {process.stderr}")
            return False
        
        logger.info("Schema applied successfully")
        return True
    except Exception as e:
        logger.error(f"Error applying schema: {str(e)}")
        return False

def check_development_connection():
    """Check development database connection"""
    try:
        logger.info("Checking development database connection...")
        conn = psycopg2.connect(DEV_DB_URI)
        conn.close()
        logger.info("Development database connection successful")
        return True
    except Exception as e:
        logger.error(f"Development database connection error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Schema synchronization utility for Mobilize CRM')
    parser.add_argument('--check', action='store_true', help='Check database connections')
    parser.add_argument('--extract', action='store_true', help='Extract schema from production')
    parser.add_argument('--apply', action='store_true', help='Apply schema to development')
    parser.add_argument('--sync', action='store_true', help='Synchronize schema (extract and apply)')
    
    args = parser.parse_args()
    
    if args.check:
        check_development_connection()
    elif args.extract:
        extract_schema_from_production()
    elif args.apply:
        schema_file = ROOT_DIR / 'schema.sql'
        if schema_file.exists():
            apply_schema_to_development(schema_file)
        else:
            logger.error(f"Schema file not found: {schema_file}")
    elif args.sync:
        schema_file = extract_schema_from_production()
        if schema_file and check_development_connection():
            apply_schema_to_development(schema_file)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
