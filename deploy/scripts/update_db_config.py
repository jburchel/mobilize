#!/usr/bin/env python3

"""
Script to update the database configuration in the application.
This script will be included in the Docker image and run at startup.
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_config_updater')

def update_config():
    """
    Update the database configuration to ensure it's using the correct DATABASE_URL.
    """
    try:
        # Get the DATABASE_URL from environment variables
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            logger.error("DATABASE_URL environment variable is not set!")
            return False
            
        # Log a masked version of the URL for debugging
        masked_url = database_url.replace('://', '://****:****@') if '://' in database_url else database_url
        logger.info(f"Using DATABASE_URL: {masked_url}")
        
        # Set the SQLAlchemy database URI environment variable
        os.environ['SQLALCHEMY_DATABASE_URI'] = database_url
        logger.info("Set SQLALCHEMY_DATABASE_URI environment variable")
        
        return True
    except Exception as e:
        logger.error(f"Error updating database configuration: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database configuration update")
    success = update_config()
    if success:
        logger.info("Database configuration updated successfully")
    else:
        logger.error("Failed to update database configuration")
