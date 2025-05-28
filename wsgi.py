#!/usr/bin/env python3
"""
WSGI entry point for the application.
This is used by production servers to run the app.
"""
import os
import logging
import time

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wsgi")

# Set the database URI environment variables before importing the app
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://postgres.fwnitauuyzxnsvgsbrzr:UK1eAogXCrBoaCyI@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require')
os.environ['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', os.environ.get('DATABASE_URL'))
os.environ['DB_CONNECTION_STRING'] = os.environ.get('DB_CONNECTION_STRING', os.environ.get('DATABASE_URL'))

# Set Supabase environment variables
os.environ['SUPABASE_URL'] = os.environ.get('SUPABASE_URL', 'https://fwnitauuyzxnsvgsbrzr.supabase.co')
os.environ['SUPABASE_KEY'] = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3bml0YXV1eXp4bnN2Z3NicnpyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDEwOTQwNzUsImV4cCI6MjA1NjY3MDA3NX0.OVhgxuiEx8kuIlQqwj5AdfcSoLUDPEM4q-6C-mtBf98')

# Ensure database URI is set before importing app
db_uri_sources = [
    os.environ.get('DATABASE_URL'),
    os.environ.get('SQLALCHEMY_DATABASE_URI'),
    os.environ.get('DB_CONNECTION_STRING'),
    'postgresql://postgres.fwnitauuyzxnsvgsbrzr:UK1eAogXCrBoaCyI@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require'
]

# Find the first non-empty database URI
db_uri = None
for uri in db_uri_sources:
    if uri:
        db_uri = uri
        logger.info(f"Found database URI in environment: {uri[:20]}...")
        break

# Set a default if none found
if not db_uri:
    logger.error("No database URI found in environment variables!")
    db_uri = 'sqlite:////tmp/default.db'
    logger.warning(f"Using default SQLite database at {db_uri}")

# Set the database URI in environment variables
os.environ['DATABASE_URL'] = db_uri
os.environ['SQLALCHEMY_DATABASE_URI'] = db_uri

# Now import the app and other modules
from app import create_app
from app.extensions import db
from app.models.office import Office
from app.models.user import User
from app.utils.setup_main_pipelines import setup_main_pipelines
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# Create the Flask application
app = create_app()

def wait_for_db_connection(app, max_retries=5, delay=2):
    """Wait for the database connection to become available."""
    for attempt in range(max_retries):
        try:
            # Try to execute a simple query to check the connection
            with app.app_context():
                db.session.execute('SELECT 1')
            logger.info("Successfully connected to the database.")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Database connection attempt {attempt + 1} failed. "
                    f"Retrying in {delay} seconds... Error: {str(e)}"
                )
                time.sleep(delay)
            else:
                logger.error("Failed to connect to the database after multiple attempts.")
                return False
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while connecting to the database: {str(e)}")
            return False
    return False

def init_minimal_data(app):
    """Initialize minimal database data if none exists."""
    with app.app_context():
        try:
            # Check if there's at least one office
            office_count = Office.query.count()
            if office_count == 0:
                logger.info("No offices found. Creating a default office...")
                office = Office(
                    name="Main Office",
                    address="123 Main St",
                    city="Springfield",
                    state="IL",
                    zip_code="62701",
                    phone="555-123-4567",
                    email="office@example.com",
                    timezone="America/New_York",
                    country="USA"
                )
                db.session.add(office)
                db.session.commit()
                logger.info("Default office created.")
            else:
                logger.info(f"Found {office_count} existing offices.")

            # Check if there's at least one admin user
            admin_count = User.query.filter_by(role='super_admin').count()
            if admin_count == 0:
                logger.info("No admin users found. Creating a default admin...")
                office = Office.query.first()
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    first_name="Admin",
                    last_name="User",
                    role="super_admin",
                    office_id=office.id
                )
                admin.set_password("password")
                db.session.add(admin)
                db.session.commit()
                logger.info("Default admin user created.")
            else:
                logger.info(f"Found {admin_count} existing admin users.")

            # Set up main pipelines if they don't exist
            logger.info("Checking for main pipelines...")
            setup_main_pipelines()
            logger.info("Pipeline initialization complete.")

        except Exception as e:
            logger.error(f"Error initializing minimal data: {str(e)}")
            db.session.rollback()

# Initialize minimal required data
if __name__ == "__main__":
    # Wait for database connection before initializing data
    if wait_for_db_connection(app):
        try:
            init_minimal_data(app)
            logger.info("Application initialization complete.")
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
    else:
        logger.error("Failed to connect to the database. Application may not function correctly.")
    
    # When running directly (not through a WSGI server)
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
else:
    # For WSGI servers (like gunicorn), wait for DB connection
    if not wait_for_db_connection(app):
        logger.error("Failed to connect to the database. Application may not function correctly.")
    else:
        try:
            init_minimal_data(app)
            logger.info("Application initialization complete.")
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")