import os
import sys
import logging

from sqlalchemy.sql import text

# Add the app directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db

"""
Script to add reminder_time column to tasks table if it doesn't exist.
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
def add_reminder_time_column():
    app = create_app()
    with app.app_context():
        try:
            logger.info("Starting migration to add reminder_time column to tasks table...")

            if not column_exists('tasks', 'reminder_time'):
                # Add reminder_time column to tasks table
                try:
                    db.session.execute(text("ALTER TABLE tasks ADD COLUMN reminder_time VARCHAR"))
                    logger.info("Successfully added reminder_time column to tasks table")
                except Exception as e:
                    logger.error(f"Error adding reminder_time column: {str(e)}")
                    db.session.rollback()
                    return
            else:
                logger.info("reminder_time column already exists in tasks table, no changes needed")

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
    add_reminder_time_column()
