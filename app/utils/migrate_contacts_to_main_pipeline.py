"""
Script to migrate existing contacts to the main pipelines.
This is used to ensure all Person and Church objects are associated with
the correct stage in the main pipeline based on their existing pipeline fields.
"""
import logging
from app import db
from app.models.office import Office
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.person import Person
from app.models.church import Church
from app.models.contact import Contact
from datetime import datetime
from flask import current_app
from sqlalchemy import select, and_, or_

logger = logging.getLogger('migration')

def get_pipeline_stages(pipeline):
    """Get all stages for a pipeline."""
    stages = {}
    for stage in pipeline.stages:
        stages[stage.name.upper()] = stage
    return stages

def migrate_contacts_to_main_pipeline():
    """
    Migrate contacts to their office's main pipeline if they're not already in it.
    Uses existing pipeline values to determine appropriate stage.
    """
    try:
        # Get all offices and their main pipelines
        offices = Office.query.all()
        office_pipelines = {}
        
        for office in offices:
            main_pipeline = Pipeline.query.filter_by(
                pipeline_type='person',
                is_main_pipeline=True,
                office_id=office.id
            ).first()
            if main_pipeline:
                office_pipelines[office.id] = {
                    'pipeline': main_pipeline,
                    'stages': get_pipeline_stages(main_pipeline)
                }

        # Process people by office
        total_people_migrated = 0
        total_churches_migrated = 0
        batch_size = 100

        for office_id, pipeline_data in office_pipelines.items():
            main_pipeline = pipeline_data['pipeline']
            stages = pipeline_data['stages']

            # Find people not in any pipeline for this office
            people_in_pipeline = db.session.query(PipelineContact.contact_id).filter(
                PipelineContact.pipeline_id == main_pipeline.id,
                PipelineContact.contact_id.isnot(None)
            ).subquery()

            # Get people who are not in the pipeline
            people_to_migrate = Person.query.filter(
                Person.office_id == office_id,
                ~Person.id.in_(db.session.query(people_in_pipeline.c.contact_id))
            ).all()

            # Process people in batches
            for i in range(0, len(people_to_migrate), batch_size):
                batch = people_to_migrate[i:i + batch_size]
                for person in batch:
                    # Determine stage based on existing pipeline value
                    stage = None
                    if person.people_pipeline and person.people_pipeline.upper() in stages:
                        stage = stages[person.people_pipeline.upper()]
                    else:
                        stage = stages.get('INFORMATION')  # Default stage

                    if stage:
                        pipeline_contact = PipelineContact(
                            pipeline_id=main_pipeline.id,
                            current_stage_id=stage.id,
                            contact_id=person.id,
                            entered_at=datetime.utcnow()
                        )
                        db.session.add(pipeline_contact)
                        total_people_migrated += 1

                db.session.commit()
                logger.info(f"Migrated batch of {len(batch)} people")

            # Find churches not in any pipeline for this office
            churches_in_pipeline = db.session.query(PipelineContact.contact_id).filter(
                PipelineContact.pipeline_id == main_pipeline.id,
                PipelineContact.contact_id.isnot(None)
            ).subquery()

            churches_to_migrate = Church.query.filter(
                Church.office_id == office_id,
                ~Church.id.in_(db.session.query(churches_in_pipeline.c.contact_id))
            ).all()

            # Process churches in batches
            for i in range(0, len(churches_to_migrate), batch_size):
                batch = churches_to_migrate[i:i + batch_size]
                for church in batch:
                    # All churches start in the INFORMATION stage
                    stage = stages.get('INFORMATION')  # Default stage

                    if stage:
                        pipeline_contact = PipelineContact(
                            pipeline_id=main_pipeline.id,
                            current_stage_id=stage.id,
                            contact_id=church.id,
                            entered_at=datetime.utcnow()
                        )
                        db.session.add(pipeline_contact)
                        total_churches_migrated += 1

                db.session.commit()
                logger.info(f"Migrated batch of {len(batch)} churches")

        logger.info(f"Migration complete. Migrated {total_people_migrated} people and {total_churches_migrated} churches.")

    except Exception as e:
        logger.error(f"Error migrating contacts to main pipelines: {str(e)}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    # This allows the script to be run directly
    from app import create_app
    app = create_app()
    with app.app_context():
        migrate_contacts_to_main_pipeline() 