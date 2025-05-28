#!/usr/bin/env python3
"""
Simple test script to verify database connection.
"""
import os
import logging
import sys
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("test_db")

def test_database_connection():
    """Test the database connection using the environment variables."""
    # Check for database URI in multiple possible environment variables
    db_uri_sources = [
        os.environ.get('DATABASE_URL'),
        os.environ.get('SQLALCHEMY_DATABASE_URI'),
        os.environ.get('DB_CONNECTION_STRING'),
        # Try different variations of the connection string
        'postgresql://postgres.fwnitauuyzxnsvgsbrzr:UK1eAogXCrBoaCyI@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require',
        'postgresql://postgres:postgres@localhost:5432/postgres',
        'sqlite:////tmp/default.db'
    ]
    
    # Find the first non-empty database URI
    db_uri = None
    for uri in db_uri_sources:
        if uri:
            db_uri = uri
            # Mask sensitive information for logging
            parsed = urlparse(uri)
            masked_uri = f"{parsed.scheme}://{parsed.netloc.split('@')[0]}:****@{parsed.netloc.split('@')[-1]}{parsed.path}"
            logger.info(f"Found database URI: {masked_uri}")
            break
    
    if not db_uri:
        logger.error("No database URI found in environment variables!")
        return False
    
    try:
        # Create engine and test connection
        engine = create_engine(db_uri)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"Database connection successful: {result.scalar() == 1}")
            
            # Get database version
            result = connection.execute(text("SELECT version()"))
            logger.info(f"Database version: {result.scalar()}")
            
            # List tables
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            logger.info(f"Tables in database: {', '.join(tables)}")
            
            return True
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing database connection...")
    success = test_database_connection()
    if success:
        logger.info("Database connection test completed successfully.")
    else:
        logger.error("Database connection test failed.")
    sys.exit(0 if success else 1)
