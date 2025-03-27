#!/usr/bin/env python3
"""
Script to assign people and churches to random pipeline stages.
This helps populate the pipeline_contacts table for testing purposes.
"""
import os
import sys
import random
from datetime import datetime

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.person import Person
from app.models.church import Church
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.extensions import db

def main():
    """Main function to assign contacts to random pipeline stages."""
    app = create_app()
    with app.app_context():
        # Find the main pipelines
        person_pipeline = Pipeline.query.filter_by(
            pipeline_type='people', 
            is_main_pipeline=True
        ).first()
        
        church_pipeline = Pipeline.query.filter_by(
            pipeline_type='church', 
            is_main_pipeline=True
        ).first()
        
        if not person_pipeline:
            print("Error: No main people pipeline found!")
            return
            
        if not church_pipeline:
            print("Error: No main church pipeline found!")
            return
            
        print(f"Found main people pipeline: {person_pipeline.name} (ID: {person_pipeline.id})")
        print(f"Found main church pipeline: {church_pipeline.name} (ID: {church_pipeline.id})")
        
        # Get all stages for each pipeline
        person_stages = PipelineStage.query.filter_by(pipeline_id=person_pipeline.id).all()
        church_stages = PipelineStage.query.filter_by(pipeline_id=church_pipeline.id).all()
        
        if not person_stages:
            print("Error: No stages found for main people pipeline!")
            return
            
        if not church_stages:
            print("Error: No stages found for main church pipeline!")
            return
            
        print(f"Found {len(person_stages)} stages for people pipeline")
        print(f"Found {len(church_stages)} stages for church pipeline")
        
        # Get all people and churches
        people = Person.query.all()
        churches = Church.query.all()
        
        print(f"Found {len(people)} people and {len(churches)} churches")
        
        # First, delete existing pipeline contacts to start fresh
        num_deleted = db.session.query(PipelineContact).delete()
        print(f"Deleted {num_deleted} existing pipeline contacts")
        
        # Assign people to random stages
        assigned_people = 0
        for person in people:
            # Don't assign all people, just a random subset
            if random.random() < 0.7:  # 70% chance of being assigned
                stage = random.choice(person_stages)
                
                pipeline_contact = PipelineContact(
                    pipeline_id=person_pipeline.id,
                    contact_id=person.id,
                    current_stage_id=stage.id,
                    entered_at=datetime.now(),
                    last_updated=datetime.now()
                )
                
                db.session.add(pipeline_contact)
                assigned_people += 1
                
        # Assign churches to random stages
        assigned_churches = 0
        for church in churches:
            # Don't assign all churches, just a random subset
            if random.random() < 0.7:  # 70% chance of being assigned
                stage = random.choice(church_stages)
                
                pipeline_contact = PipelineContact(
                    pipeline_id=church_pipeline.id,
                    contact_id=church.id,
                    current_stage_id=stage.id,
                    entered_at=datetime.now(),
                    last_updated=datetime.now()
                )
                
                db.session.add(pipeline_contact)
                assigned_churches += 1
        
        # Commit changes
        db.session.commit()
        
        print(f"Successfully assigned {assigned_people} people to random stages in the main people pipeline")
        print(f"Successfully assigned {assigned_churches} churches to random stages in the main church pipeline")
        
        # Verify the assignments by querying the pipeline_contacts table
        person_contacts = db.session.query(PipelineContact).filter_by(
            pipeline_id=person_pipeline.id
        ).join(Person, PipelineContact.contact_id == Person.id).count()
        
        church_contacts = db.session.query(PipelineContact).filter_by(
            pipeline_id=church_pipeline.id
        ).join(Church, PipelineContact.contact_id == Church.id).count()
        
        print(f"Verification: {person_contacts} people and {church_contacts} churches are now in pipelines")
        
        # List count of contacts per stage for people pipeline
        print("\nPeople pipeline stage distribution:")
        for stage in person_stages:
            count = db.session.query(PipelineContact).filter_by(
                pipeline_id=person_pipeline.id,
                current_stage_id=stage.id
            ).count()
            print(f"  - {stage.name}: {count} contacts")
        
        # List count of contacts per stage for church pipeline
        print("\nChurch pipeline stage distribution:")
        for stage in church_stages:
            count = db.session.query(PipelineContact).filter_by(
                pipeline_id=church_pipeline.id,
                current_stage_id=stage.id
            ).count()
            print(f"  - {stage.name}: {count} contacts")


if __name__ == "__main__":
    main() 