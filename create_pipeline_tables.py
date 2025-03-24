#!/usr/bin/env python
"""
Script to create pipeline tables directly in the database.
This is a workaround for when migrations aren't working properly.
"""
from app import create_app
from flask import current_app
from app.extensions import db
from datetime import datetime
import os
import sys

def create_tables():
    """Create pipeline tables."""
    # Import models here to avoid circular imports
    from app.models.pipeline import Pipeline, PipelineStage, PipelineContact, PipelineStageHistory
    
    app = create_app()
    with app.app_context():
        # Check if tables already exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        pipeline_tables = ['pipelines', 'pipeline_stages', 'pipeline_contacts', 'pipeline_stage_history']
        existing_tables = [t for t in pipeline_tables if t in tables]
        missing_tables = [t for t in pipeline_tables if t not in tables]
        
        if not missing_tables:
            print("All pipeline tables already exist!")
            return
            
        print(f"Existing tables: {existing_tables}")
        print(f"Missing tables: {missing_tables}")
        
        # Create tables
        try:
            # Create specific tables rather than all tables
            if 'pipelines' in missing_tables:
                Pipeline.__table__.create(db.engine)
                print("Created pipelines table")
                
            if 'pipeline_stages' in missing_tables:
                PipelineStage.__table__.create(db.engine)
                print("Created pipeline_stages table")
                
            if 'pipeline_contacts' in missing_tables:
                PipelineContact.__table__.create(db.engine)
                print("Created pipeline_contacts table")
                
            if 'pipeline_stage_history' in missing_tables:
                PipelineStageHistory.__table__.create(db.engine)
                print("Created pipeline_stage_history table")
                
            print("Pipeline tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise

if __name__ == "__main__":
    create_tables() 