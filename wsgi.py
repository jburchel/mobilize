#!/usr/bin/env python3
"""
WSGI entry point for the application.
This is used by production servers to run the app.
"""
import os
import sys
import logging

from app import create_app
from app.extensions import db
from app.models.office import Office
from app.models.user import User
from app.utils.setup_main_pipelines import setup_main_pipelines

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wsgi")

app = create_app()

def init_minimal_data():
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
init_minimal_data()

if __name__ == "__main__":
    # When running directly (not through a WSGI server)
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"]) 