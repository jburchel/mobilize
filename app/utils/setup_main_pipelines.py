"""
Script to set up the main people and church pipelines.
These are the system pipelines that all contacts are categorized by.
"""
from app.extensions import db
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.constants import PEOPLE_PIPELINE_CHOICES, CHURCH_PIPELINE_CHOICES
from app.models.office import Office
from datetime import datetime
import logging

logger = logging.getLogger('setup')

def setup_main_pipelines():
    """Set up the main pipelines for people and churches if they don't exist."""
    logger.info("Checking for main pipelines")
    
    # Get all offices
    offices = Office.query.all()
    if not offices:
        logger.warning("No offices found. Please create offices first.")
        return
    
    for office in offices:
        logger.info(f"Setting up pipelines for office: {office.name}")
        
        # Setup People main pipeline for this office
        people_pipeline = Pipeline.query.filter_by(
            office_id=office.id,
            pipeline_type="people",
            is_main_pipeline=True
        ).first()
        
        if not people_pipeline:
            logger.info(f"Creating People main pipeline for {office.name}")
            people_pipeline = Pipeline(
                name=f"{office.name} People Pipeline",
                pipeline_type="people",
                office_id=office.id,
                is_main_pipeline=True,
                description=f"Main pipeline for tracking people contacts in {office.name}"
            )
            db.session.add(people_pipeline)
            db.session.flush()  # Get the ID before adding stages
        else:
            # First, delete any pipeline_contacts related to these stages
            logger.info(f"Deleting existing pipeline contacts for People main pipeline in {office.name}")
            PipelineContact.query.filter_by(pipeline_id=people_pipeline.id).delete()
            
            # Then delete existing stages for people pipeline to reset
            logger.info(f"Resetting People main pipeline stages for {office.name}")
            PipelineStage.query.filter_by(pipeline_id=people_pipeline.id).delete()
            db.session.flush()
        
        # Create default stages for people based on constants
        for i, stage_choice in enumerate(PEOPLE_PIPELINE_CHOICES):
            stage_name = stage_choice[0]
            # Define colors for each stage
            colors = ["#3498db", "#2ecc71", "#f1c40f", "#e67e22", "#e74c3c", "#9b59b6"]
            color = colors[i % len(colors)]
            
            stage = PipelineStage(
                pipeline_id=people_pipeline.id,
                name=stage_name,
                order=i + 1,
                color=color,
                description=f"Standard {stage_name} stage for people"
            )
            db.session.add(stage)
        
        logger.info(f"Created/updated stages for People main pipeline in {office.name}")
        
        # Setup Church main pipeline for this office
        church_pipeline = Pipeline.query.filter_by(
            office_id=office.id,
            pipeline_type="church",
            is_main_pipeline=True
        ).first()
        
        if not church_pipeline:
            logger.info(f"Creating Church main pipeline for {office.name}")
            church_pipeline = Pipeline(
                name=f"{office.name} Church Pipeline",
                pipeline_type="church",
                office_id=office.id,
                is_main_pipeline=True,
                description=f"Main pipeline for tracking church contacts in {office.name}"
            )
            db.session.add(church_pipeline)
            db.session.flush()  # Get the ID before adding stages
        else:
            # First, delete any pipeline_contacts related to these stages
            logger.info(f"Deleting existing pipeline contacts for Church main pipeline in {office.name}")
            PipelineContact.query.filter_by(pipeline_id=church_pipeline.id).delete()
            
            # Then delete existing stages for church pipeline to reset
            logger.info(f"Resetting Church main pipeline stages for {office.name}")
            PipelineStage.query.filter_by(pipeline_id=church_pipeline.id).delete()
            db.session.flush()
        
        # Create default stages for churches based on constants
        for i, stage_choice in enumerate(CHURCH_PIPELINE_CHOICES):
            stage_name = stage_choice[0]
            # Define colors for each stage
            colors = ["#3498db", "#2ecc71", "#f1c40f", "#e67e22", "#e74c3c", "#9b59b6"]
            color = colors[i % len(colors)]
            
            stage = PipelineStage(
                pipeline_id=church_pipeline.id,
                name=stage_name,
                order=i + 1,
                color=color,
                description=f"Standard {stage_name} stage for churches"
            )
            db.session.add(stage)
        
        logger.info(f"Created/updated stages for Church main pipeline in {office.name}")
    
    # Commit changes
    db.session.commit()
    logger.info("Main pipelines setup complete")

def get_stage_color(index):
    """Return a color for the stage based on index."""
    colors = ["#3498db", "#2ecc71", "#f1c40f", "#e74c3c", "#9b59b6", "#1abc9c"]
    return colors[index % len(colors)]

if __name__ == "__main__":
    # This allows the script to be run directly
    from app import create_app
    app = create_app()
    with app.app_context():
        setup_main_pipelines() 