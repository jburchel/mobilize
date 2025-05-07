#!/usr/bin/env python
"""
Database synchronization utility for Mobilize CRM

This script helps manage database migrations and synchronization between
development and production environments using the same PostgreSQL database.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db-sync')

# Get the application root directory
ROOT_DIR = Path(__file__).parent.parent.absolute()

# Load environment variables
load_dotenv(ROOT_DIR / '.env.development')

def run_migrations():
    """Run database migrations"""
    try:
        logger.info("Running database migrations...")
        from flask_migrate import upgrade
        from app import create_app
        
        app = create_app()
        with app.app_context():
            upgrade()
        logger.info("Migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        sys.exit(1)

def check_database_connection():
    """Check database connection"""
    try:
        logger.info("Checking database connection...")
        from sqlalchemy import create_engine
        from sqlalchemy.exc import SQLAlchemyError
        
        db_uri = os.getenv('DB_CONNECTION_STRING')
        if not db_uri:
            logger.error("DB_CONNECTION_STRING environment variable not set")
            sys.exit(1)
            
        engine = create_engine(db_uri)
        connection = engine.connect()
        connection.close()
        logger.info("Database connection successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error checking database connection: {str(e)}")
        return False

def create_tables():
    """Create database tables"""
    try:
        logger.info("Creating database tables...")
        from app import create_app
        
        app = create_app()
        with app.app_context():
            from app.extensions import db
            db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Database synchronization utility for Mobilize CRM')
    parser.add_argument('--check', action='store_true', help='Check database connection')
    parser.add_argument('--migrate', action='store_true', help='Run database migrations')
    parser.add_argument('--create-tables', action='store_true', help='Create database tables')
    
    args = parser.parse_args()
    
    if args.check:
        check_database_connection()
    elif args.migrate:
        if check_database_connection():
            run_migrations()
        else:
            logger.error("Cannot run migrations due to database connection issues")
            sys.exit(1)
    elif args.create_tables:
        if check_database_connection():
            create_tables()
        else:
            logger.error("Cannot create tables due to database connection issues")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
