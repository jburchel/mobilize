#!/usr/bin/env python3
"""
Script to clean up pipeline data and regenerate it.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app, db
from app.models.pipeline import PipelineContact, PipelineStageHistory, PipelineStage, Pipeline
from app.utils.setup_main_pipelines import setup_main_pipelines
from scripts.generate_sample_data import create_sample_pipeline_data

def clean_pipeline_data():
    """Clean up pipeline data and regenerate it."""
    print("Cleaning up pipeline data...")
    
    try:
        # Create application context
        app = create_app()
        
        with app.app_context():
            # Delete all pipeline data
            print("Deleting all pipeline contacts and stage history...")
            PipelineContact.query.delete()
            PipelineStageHistory.query.delete()
            
            print("Deleting all pipeline stages...")
            PipelineStage.query.delete()
            
            print("Deleting all pipelines...")
            Pipeline.query.delete()
            
            db.session.commit()
            print("✅ Pipeline data cleaned.")
            
            print("\nSetting up main pipelines...")
            setup_main_pipelines()
            print("✅ Main pipelines set up.")
            
            print("\nRegenerating pipeline data...")
            # Get all offices
            from app.models.office import Office
            offices = Office.query.all()
            
            # Regenerate pipeline data
            create_sample_pipeline_data(offices)
            print("✅ Pipeline data regenerated.")
            
    except Exception as e:
        print(f"\n❌ Error during pipeline data cleanup: {str(e)}")
        print("\nFull error traceback:")
        import traceback
        print(traceback.format_exc())
        return

if __name__ == "__main__":
    clean_pipeline_data() 