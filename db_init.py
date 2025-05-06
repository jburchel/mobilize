"""
Database initialization script.
This script initializes the PostgreSQL database schema.
"""
import os
import sys
import logging
import shutil
from app import create_app
from app.models.relationships import setup_relationships
from app.models.user import User
from app.utils.setup_main_pipelines import setup_main_pipelines
from app.utils.ensure_church_pipeline import init_app as init_church_pipeline
from app.extensions import db

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db-init')

# Set environment variables
os.environ['FLASK_APP'] = 'app.py'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'
os.environ['SKIP_DB_INIT'] = 'False'  # Force DB init

# Ensure logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')
    logger.info("Created logs directory")

# Create a backup of migrations directory if it exists
if os.path.exists('migrations'):
    logger.info("Creating backup of migrations directory")
    if os.path.exists('migrations.bak'):
        shutil.rmtree('migrations.bak')
    shutil.copytree('migrations', 'migrations.bak')

# Initialize the application
logger.info("Initializing application and database...")

# Explicitly setup relationships
try:
    setup_relationships()
    logger.info("Model relationships set up successfully")
except Exception as e:
    logger.error(f"Error setting up relationships: {str(e)}")
    sys.exit(1)

# Create app and database
try:
    app = create_app()
    with app.app_context():
        from app.extensions import db
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Initialize pipelines
        from app.utils.setup_main_pipelines import setup_main_pipelines
        setup_main_pipelines()
        logger.info("Pipelines initialized")
        
        # Initialize church pipeline
        from app.utils.ensure_church_pipeline import init_app as init_church_pipeline
        init_church_pipeline(app)
        logger.info("Church pipeline initialized")
        
        # Create test user only in development environment
        from app.models.user import User
        if os.environ.get('FLASK_ENV') == 'development':
            if not User.query.filter_by(email='test@example.com').first():
                test_user = User(
                    email='test@example.com',
                    username='testuser',
                    firebase_uid='dev-test-user',
                    first_name='Test',
                    last_name='User',
                    role='super_admin',
                    office_id=1,
                    is_active=True,
                    first_login=False
                )
                db.session.add(test_user)
                db.session.commit()
                logger.info("Created test user for development environment")
            else:
                logger.info("Test user already exists")
        else:
            logger.info("Skipping test user creation in production environment")
    
    logger.info("Database initialization complete.")
    logger.info("You can now run the app with: python run_dev.py")
    
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")
    sys.exit(1) 