"""
Script to set up the main people and church pipelines.
These are the system pipelines that all contacts are categorized by.
"""
from app.extensions import db
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.constants import PEOPLE_PIPELINE_CHOICES, CHURCH_PIPELINE_CHOICES
from app.models.person import Person
from app.models.church import Church
from datetime import datetime
import logging

logger = logging.getLogger('setup')

def setup_main_pipelines():
    """Set up a single universal main people and church pipeline, and assign all people/churches to it."""
    logger.info("Checking for universal main pipelines")

    # --- PEOPLE PIPELINE ---
    people_pipeline = Pipeline.query.filter_by(
        pipeline_type="people",
        is_main_pipeline=True
    ).first()

    if not people_pipeline:
        logger.info(f"Creating universal Main People Pipeline")
        people_pipeline = Pipeline(
            name="Mobilize Global HQ People Pipeline",
            pipeline_type="people",
            is_main_pipeline=True,
            description="Main pipeline for tracking people contacts (universal)"
        )
        db.session.add(people_pipeline)
        db.session.flush()  # Get the ID before adding stages
    else:
        # Remove all pipeline contacts and stages for reset
        PipelineContact.query.filter_by(pipeline_id=people_pipeline.id).delete()
        PipelineStage.query.filter_by(pipeline_id=people_pipeline.id).delete()
        db.session.flush()

    # Create default stages for people
    stage_ids = []
    for i, stage_choice in enumerate(PEOPLE_PIPELINE_CHOICES):
        stage_name = stage_choice[0]
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
        db.session.flush()
        stage_ids.append(stage.id)
    db.session.flush()

    # Assign all people to the first stage of the main pipeline
    first_stage_id = stage_ids[0] if stage_ids else None
    if first_stage_id:
        people = Person.query.all()
        for person in people:
            pc = PipelineContact(
                pipeline_id=people_pipeline.id,
                contact_id=person.id,
                current_stage_id=first_stage_id,
                entered_at=datetime.now(),
                last_updated=datetime.now()
            )
            db.session.add(pc)
    logger.info(f"Assigned all people to main pipeline stage: {PEOPLE_PIPELINE_CHOICES[0][0]}")

    # --- CHURCH PIPELINE ---
    church_pipeline = Pipeline.query.filter_by(
        pipeline_type="church",
        is_main_pipeline=True
    ).first()

    if not church_pipeline:
        logger.info(f"Creating universal Main Church Pipeline")
        church_pipeline = Pipeline(
            name="Mobilize Global HQ Church Pipeline",
            pipeline_type="church",
            is_main_pipeline=True,
            description="Main pipeline for tracking church contacts (universal)"
        )
        db.session.add(church_pipeline)
        db.session.flush()
    else:
        PipelineContact.query.filter_by(pipeline_id=church_pipeline.id).delete()
        PipelineStage.query.filter_by(pipeline_id=church_pipeline.id).delete()
        db.session.flush()

    # Create default stages for churches
    church_stage_ids = []
    for i, stage_choice in enumerate(CHURCH_PIPELINE_CHOICES):
        stage_name = stage_choice[0]
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
        db.session.flush()
        church_stage_ids.append(stage.id)
    db.session.flush()

    # Assign all churches to the first stage of the main church pipeline
    first_church_stage_id = church_stage_ids[0] if church_stage_ids else None
    if first_church_stage_id:
        churches = Church.query.all()
        for church in churches:
            pc = PipelineContact(
                pipeline_id=church_pipeline.id,
                contact_id=church.id,
                current_stage_id=first_church_stage_id,
                entered_at=datetime.now(),
                last_updated=datetime.now()
            )
            db.session.add(pc)
    logger.info(f"Assigned all churches to main pipeline stage: {CHURCH_PIPELINE_CHOICES[0][0]}")

    db.session.commit()
    logger.info("Universal main pipelines setup complete")

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