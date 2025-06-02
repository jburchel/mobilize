import os
import sys
import logging

from sqlalchemy.sql import text

# Add the app directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db

"""
Script to add church_name column to contacts table if it doesn't exist.
"""

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to check if a column exists in a table
def column_exists(table_name, column_name):
    try:
        result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :table_name AND column_name = :column_name"), {'table_name': table_name, 'column_name': column_name})
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking if column {column_name} exists in {table_name}: {str(e)}")
        return False

# Create the Flask app context
def add_church_name_column():
    app = create_app()
    with app.app_context():
        try:
            logger.info("Starting migration to add church_name column to contacts table...")

            if not column_exists('contacts', 'church_name'):
                # Add church_name column to contacts table
                try:
                    db.session.execute(text("ALTER TABLE contacts ADD COLUMN church_name VARCHAR(100)"))
                    logger.info("Successfully added church_name column to contacts table")
                except Exception as e:
                    logger.error(f"Error adding church_name column: {str(e)}")
                    db.session.rollback()
                    return
            else:
                logger.info("church_name column already exists in contacts table, no changes needed")

            # Commit changes to the database
            try:
                db.session.commit()
                logger.info("Successfully completed migration.")
            except Exception as e:
                logger.error(f"Error committing changes to database: {str(e)}")
                db.session.rollback()
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    add_church_name_column()
