#!/usr/bin/env python3

"""
Script to fix database transaction issues in the Flask application.

This script creates a patch file that adds automatic transaction rollback
handling to the Flask application to prevent 'transaction is aborted' errors.

Usage:
    python3 fix_db_transaction.py
"""

import os
import sys

def create_patch_file():
    """Create a patch file to fix database transaction handling."""
    patch_content = """
# db_transaction_fix.py
"""Database transaction fix for SQLAlchemy.

This module adds request handlers to automatically rollback aborted transactions.
"""
from flask import Flask, g, request, current_app
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

def init_app(app):
    """Initialize the database transaction fix."""
    @app.before_request
    def ensure_db_session():
        """Ensure a fresh database session at the start of each request."""
        # Store the original session on the g object for reference
        g.original_db_session = db.session
        
        # Check if we need to rollback any existing transaction
        try:
            # Try a simple query to check if the session is usable
            db.session.execute("SELECT 1")
        except SQLAlchemyError as e:
            logger.warning(f"Database session error detected, rolling back: {str(e)}")
            try:
                db.session.rollback()
                logger.info("Successfully rolled back transaction")
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {str(rollback_error)}")
                # Create a new session as a last resort
                db.session.remove()
                db.session = db.create_scoped_session()
                logger.info("Created new database session")
    
    @app.teardown_request
    def cleanup_db_session(exception=None):
        """Clean up the database session at the end of each request."""
        if exception:
            logger.warning(f"Exception during request, rolling back transaction: {str(exception)}")
            try:
                db.session.rollback()
            except Exception as e:
                logger.error(f"Error during rollback in teardown: {str(e)}")
        
        # Always close the session at the end of the request
        try:
            db.session.close()
        except Exception as e:
            logger.error(f"Error closing session: {str(e)}")
"""
    
    # Write the patch file
    patch_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app', 'utils', 'db_transaction_fix.py')
    os.makedirs(os.path.dirname(patch_file_path), exist_ok=True)
    
    with open(patch_file_path, 'w') as f:
        f.write(patch_content)
    
    print(f"Created patch file: {patch_file_path}")
    
    # Now modify app/__init__.py to use the patch
    init_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app', '__init__.py')
    
    if not os.path.exists(init_file_path):
        print(f"Error: Could not find {init_file_path}")
        return False
    
    with open(init_file_path, 'r') as f:
        init_content = f.read()
    
    # Add import for the patch
    import_line = "from app.utils.db_transaction_fix import init_app as init_db_transaction_fix"
    if import_line not in init_content:
        # Find the last import line
        import_lines = [line for line in init_content.split('\n') if line.startswith('from ') or line.startswith('import ')]
        last_import_line = import_lines[-1]
        
        # Insert our import after the last import
        init_content = init_content.replace(last_import_line, last_import_line + '\n' + import_line)
    
    # Add initialization of the patch
    init_patch_line = "    # Initialize database transaction fix\n    init_db_transaction_fix(app)"
    if init_patch_line not in init_content:
        # Find a good place to insert the initialization
        # Look for the line after extensions are initialized
        target_line = "    # Initialize extensions"
        if target_line in init_content:
            # Find the next line that's not a comment or blank
            lines = init_content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == target_line:
                    # Find the next non-comment, non-blank line
                    for j in range(i+1, len(lines)):
                        if lines[j].strip() and not lines[j].strip().startswith('#'):
                            # Insert our initialization after this line
                            lines.insert(j+1, init_patch_line)
                            init_content = '\n'.join(lines)
                            break
                    break
        else:
            # Alternative insertion point: after db initialization
            target_line = "    db.init_app(app)"
            if target_line in init_content:
                init_content = init_content.replace(target_line, target_line + '\n' + init_patch_line)
    
    # Write the modified init file
    with open(init_file_path, 'w') as f:
        f.write(init_content)
    
    print(f"Updated {init_file_path} to use the database transaction fix")
    
    # Create a Dockerfile to build the patched application
    dockerfile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Dockerfile.patched')
    dockerfile_content = """
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app \
    FLASK_ENV=production \
    OAUTHLIB_INSECURE_TRANSPORT=0 \
    PREFERRED_URL_SCHEME=https

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD gunicorn --bind :8080 --workers 2 --threads 8 --timeout 0 'app:create_app()'
"""
    
    with open(dockerfile_path, 'w') as f:
        f.write(dockerfile_content)
    
    print(f"Created patched Dockerfile: {dockerfile_path}")
    
    # Create a deployment script
    deploy_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deploy_patched_app.sh')
    deploy_script_content = """
#!/bin/bash

set -e

echo "Building patched Docker image..."
gcloud builds submit --tag gcr.io/mobilize-crm/mobilize-crm:patched

echo "Deploying patched application to Cloud Run..."
gcloud run deploy mobilize-crm \
    --image gcr.io/mobilize-crm/mobilize-crm:patched \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars FLASK_APP=app,FLASK_ENV=production,OAUTHLIB_INSECURE_TRANSPORT=0,PREFERRED_URL_SCHEME=https \
    --update-secrets=DB_CONNECTION_STRING=DB_CONNECTION_STRING:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,BASE_URL=BASE_URL:latest

echo "Deployment complete!"
"""
    
    with open(deploy_script_path, 'w') as f:
        f.write(deploy_script_content)
    
    os.chmod(deploy_script_path, 0o755)  # Make the script executable
    
    print(f"Created deployment script: {deploy_script_path}")
    print("\nTo deploy the patched application, run:")
    print(f"  {deploy_script_path}")
    
    return True

if __name__ == "__main__":
    success = create_patch_file()
    if success:
        print("\nDatabase transaction fix created successfully!")
    else:
        print("\nFailed to create database transaction fix")
        sys.exit(1)
