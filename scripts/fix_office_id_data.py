import os
import sys
import logging
from sqlalchemy.sql import text

# Add the app directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db

"""
Script to fix office_id data integrity issues in the database by ensuring all office_id values are integers.
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
def fix_office_id_data():
    app = create_app()
    with app.app_context():
        try:
            logger.info("Starting office_id data integrity fix...")

            # Fix Person records (assuming table name is 'people')
            try:
                if column_exists('people', 'office_id'):
                    result = db.session.execute(text("SELECT id, office_id FROM people"))
                    for row in result:
                        if row.office_id and isinstance(row.office_id, str):
                            try:
                                office_id_int = int(row.office_id)
                                db.session.execute(text("UPDATE people SET office_id = :office_id WHERE id = :id"), {'office_id': office_id_int, 'id': row.id})
                                logger.info(f"Converted office_id for Person ID {row.id} from string to integer")
                            except ValueError:
                                logger.warning(f"Invalid office_id format for Person ID {row.id}, setting to NULL")
                                db.session.execute(text("UPDATE people SET office_id = NULL WHERE id = :id"), {'id': row.id})
                else:
                    logger.info("office_id column does not exist in people table, skipping...")
            except Exception as e:
                logger.error(f"Error querying/updating Person records: {str(e)}")
                db.session.rollback()

            # Fix Church records (assuming table name is 'churches')
            try:
                if column_exists('churches', 'office_id'):
                    result = db.session.execute(text("SELECT id, office_id FROM churches"))
                    for row in result:
                        if row.office_id and isinstance(row.office_id, str):
                            try:
                                office_id_int = int(row.office_id)
                                db.session.execute(text("UPDATE churches SET office_id = :office_id WHERE id = :id"), {'office_id': office_id_int, 'id': row.id})
                                logger.info(f"Converted office_id for Church ID {row.id} from string to integer")
                            except ValueError:
                                logger.warning(f"Invalid office_id format for Church ID {row.id}, setting to NULL")
                                db.session.execute(text("UPDATE churches SET office_id = NULL WHERE id = :id"), {'id': row.id})
                else:
                    logger.info("office_id column does not exist in churches table, skipping...")
            except Exception as e:
                logger.error(f"Error querying/updating Church records: {str(e)}")
                db.session.rollback()

            # Fix Communication records (assuming table name is 'communications')
            try:
                if column_exists('communications', 'office_id'):
                    result = db.session.execute(text("SELECT id, office_id FROM communications"))
                    for row in result:
                        if row.office_id and isinstance(row.office_id, str):
                            try:
                                office_id_int = int(row.office_id)
                                db.session.execute(text("UPDATE communications SET office_id = :office_id WHERE id = :id"), {'office_id': office_id_int, 'id': row.id})
                                logger.info(f"Converted office_id for Communication ID {row.id} from string to integer")
                            except ValueError:
                                logger.warning(f"Invalid office_id format for Communication ID {row.id}, setting to NULL")
                                db.session.execute(text("UPDATE communications SET office_id = NULL WHERE id = :id"), {'id': row.id})
                else:
                    logger.info("office_id column does not exist in communications table, skipping...")
            except Exception as e:
                logger.error(f"Error querying/updating Communication records: {str(e)}")
                db.session.rollback()

            # Fix Task records (assuming table name is 'tasks')
            try:
                if column_exists('tasks', 'office_id'):
                    result = db.session.execute(text("SELECT id, office_id FROM tasks"))
                    for row in result:
                        if row.office_id and isinstance(row.office_id, str):
                            try:
                                office_id_int = int(row.office_id)
                                db.session.execute(text("UPDATE tasks SET office_id = :office_id WHERE id = :id"), {'office_id': office_id_int, 'id': row.id})
                                logger.info(f"Converted office_id for Task ID {row.id} from string to integer")
                            except ValueError:
                                logger.warning(f"Invalid office_id format for Task ID {row.id}, setting to NULL")
                                db.session.execute(text("UPDATE tasks SET office_id = NULL WHERE id = :id"), {'id': row.id})
                else:
                    logger.info("office_id column does not exist in tasks table, skipping...")
            except Exception as e:
                logger.error(f"Error querying/updating Task records: {str(e)}")
                db.session.rollback()

            # Commit changes to the database
            try:
                db.session.commit()
                logger.info("Successfully completed office_id data integrity fix.")
            except Exception as e:
                logger.error(f"Error committing changes to database: {str(e)}")
                db.session.rollback()
        except Exception as e:
            logger.error(f"Error during office_id data fix: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    fix_office_id_data()
