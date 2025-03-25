#!/usr/bin/env python3
"""
Script to populate pipelines with existing contacts and create custom pipelines
"""
from app import create_app, db
from app.models import Pipeline, PipelineStage, PipelineContact, Contact, Person, Church, PipelineStageHistory, Office
from datetime import datetime
import random
import sys
import traceback

app = create_app()

def distribute_contacts_to_main_pipelines():
    """Distribute existing contacts to main pipelines randomly across stages"""
    with app.app_context():
        print("Starting distribute_contacts_to_main_pipelines function...")
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Print information about all offices
        offices = Office.query.all()
        print(f"Found {len(offices)} offices in the database:")
        for office in offices:
            print(f"  Office: {office.name} (ID: {office.id})")
        
        # Get main pipelines
        main_people_pipelines = Pipeline.query.filter_by(is_main_pipeline=True, pipeline_type="people").all()
        main_church_pipelines = Pipeline.query.filter_by(is_main_pipeline=True, pipeline_type="church").all()
        
        if not main_people_pipelines or not main_church_pipelines:
            print("Main pipelines not found. Please run the setup script first.")
            return
        
        print(f"Found {len(main_people_pipelines)} main people pipelines:")
        for pipeline in main_people_pipelines:
            print(f"  ID: {pipeline.id}, Name: {pipeline.name}, Office ID: {pipeline.office_id}")
        
        print(f"Found {len(main_church_pipelines)} main church pipelines:")
        for pipeline in main_church_pipelines:
            print(f"  ID: {pipeline.id}, Name: {pipeline.name}, Office ID: {pipeline.office_id}")
        
        # First, clear any existing pipeline contacts to avoid duplicates
        print("Clearing existing pipeline contacts...")
        try:
            original_people_contacts_count = PipelineContact.query.join(Pipeline).filter(
                Pipeline.is_main_pipeline == True, 
                Pipeline.pipeline_type == "people"
            ).count()
            
            original_church_contacts_count = PipelineContact.query.join(Pipeline).filter(
                Pipeline.is_main_pipeline == True, 
                Pipeline.pipeline_type == "church"
            ).count()
            
            print(f"Original people pipeline contacts: {original_people_contacts_count}")
            print(f"Original church pipeline contacts: {original_church_contacts_count}")
            
            # Delete all pipeline contacts for main pipelines
            deleted_people = PipelineContact.query.join(Pipeline).filter(
                Pipeline.is_main_pipeline == True, 
                Pipeline.pipeline_type == "people"
            ).delete(synchronize_session=False)
            
            deleted_churches = PipelineContact.query.join(Pipeline).filter(
                Pipeline.is_main_pipeline == True, 
                Pipeline.pipeline_type == "church"
            ).delete(synchronize_session=False)
            
            db.session.commit()
            print(f"Deleted {deleted_people} people pipeline contacts")
            print(f"Deleted {deleted_churches} church pipeline contacts")
        except Exception as e:
            print(f"Error clearing pipeline contacts: {str(e)}")
            traceback.print_exc()
            db.session.rollback()
        
        # Verify contacts were deleted
        after_delete_people = PipelineContact.query.join(Pipeline).filter(
            Pipeline.is_main_pipeline == True, 
            Pipeline.pipeline_type == "people"
        ).count()
        
        after_delete_church = PipelineContact.query.join(Pipeline).filter(
            Pipeline.is_main_pipeline == True, 
            Pipeline.pipeline_type == "church"
        ).count()
        
        print(f"After delete - people pipeline contacts: {after_delete_people}")
        print(f"After delete - church pipeline contacts: {after_delete_church}")
        
        # Get all people and churches
        people = Person.query.all()
        churches = Church.query.all()
        
        print(f"Found {len(people)} people to distribute")
        print(f"Found {len(churches)} churches to distribute")
        
        # Reset counters
        total_people_added = 0
        total_churches_added = 0
        
        # Process each main people pipeline
        for main_people_pipeline in main_people_pipelines:
            people_stages = PipelineStage.query.filter_by(pipeline_id=main_people_pipeline.id).all()
            
            if not people_stages:
                print(f"No stages found for pipeline {main_people_pipeline.name} (ID: {main_people_pipeline.id})")
                continue
                
            print(f"\nDistributing people to {main_people_pipeline.name} (ID: {main_people_pipeline.id})...")
            print(f"Found {len(people_stages)} stages for this pipeline")
            
            # Get people for this office
            office_people = [p for p in people if p.office_id == main_people_pipeline.office_id]
            print(f"Found {len(office_people)} people for office_id {main_people_pipeline.office_id}")
            
            people_success = 0
            people_errors = 0
            
            for person in office_people:
                try:
                    # Select a random stage
                    random_stage = random.choice(people_stages)
                    
                    # Create pipeline contact
                    pipeline_contact = PipelineContact(
                        pipeline_id=main_people_pipeline.id,
                        contact_id=person.id,
                        current_stage_id=random_stage.id,
                        entered_at=datetime.now(),
                        last_updated=datetime.now()
                    )
                    db.session.add(pipeline_contact)
                    
                    # We need to flush first to get the ID
                    db.session.flush()
                    
                    # Create history entry
                    history = PipelineStageHistory(
                        pipeline_contact_id=pipeline_contact.id,
                        to_stage_id=random_stage.id,
                        created_by_id=1,  # Admin user
                        notes="Initial stage assignment",
                        created_at=datetime.now()
                    )
                    db.session.add(history)
                    
                    # Commit every person immediately to avoid transaction issues
                    db.session.commit()
                    people_success += 1
                    total_people_added += 1
                    
                    if people_success % 5 == 0:
                        print(f"  Added {people_success} people to {main_people_pipeline.name}")
                        
                except Exception as e:
                    people_errors += 1
                    print(f"Error adding person ID {person.id} to pipeline {main_people_pipeline.id}: {str(e)}")
                    traceback.print_exc()
                    db.session.rollback()
            
            print(f"Pipeline {main_people_pipeline.name} - People success: {people_success}, errors: {people_errors}")
            
            # Verify people were added
            pipeline_people_count = PipelineContact.query.filter_by(pipeline_id=main_people_pipeline.id).count()
            print(f"Verification: {pipeline_people_count} people in pipeline {main_people_pipeline.name}")
        
        # Process each main church pipeline
        for main_church_pipeline in main_church_pipelines:
            church_stages = PipelineStage.query.filter_by(pipeline_id=main_church_pipeline.id).all()
            
            if not church_stages:
                print(f"No stages found for pipeline {main_church_pipeline.name} (ID: {main_church_pipeline.id})")
                continue
                
            print(f"\nDistributing churches to {main_church_pipeline.name} (ID: {main_church_pipeline.id})...")
            print(f"Found {len(church_stages)} stages for this pipeline")
            
            # Get churches for this office
            office_churches = [c for c in churches if c.office_id == main_church_pipeline.office_id]
            print(f"Found {len(office_churches)} churches for office_id {main_church_pipeline.office_id}")
            
            church_success = 0
            church_errors = 0
            
            for church in office_churches:
                try:
                    # Select a random stage
                    random_stage = random.choice(church_stages)
                    
                    # Create pipeline contact
                    pipeline_contact = PipelineContact(
                        pipeline_id=main_church_pipeline.id,
                        contact_id=church.id,
                        current_stage_id=random_stage.id,
                        entered_at=datetime.now(),
                        last_updated=datetime.now()
                    )
                    db.session.add(pipeline_contact)
                    
                    # We need to flush first to get the ID
                    db.session.flush()
                    
                    # Create history entry
                    history = PipelineStageHistory(
                        pipeline_contact_id=pipeline_contact.id,
                        to_stage_id=random_stage.id,
                        created_by_id=1,  # Admin user
                        notes="Initial stage assignment",
                        created_at=datetime.now()
                    )
                    db.session.add(history)
                    
                    # Commit every church immediately to avoid transaction issues
                    db.session.commit()
                    church_success += 1
                    total_churches_added += 1
                    
                    if church_success % 5 == 0:
                        print(f"  Added {church_success} churches to {main_church_pipeline.name}")
                        
                except Exception as e:
                    church_errors += 1
                    print(f"Error adding church ID {church.id} to pipeline {main_church_pipeline.id}: {str(e)}")
                    traceback.print_exc()
                    db.session.rollback()
            
            print(f"Pipeline {main_church_pipeline.name} - Churches success: {church_success}, errors: {church_errors}")
            
            # Verify churches were added
            pipeline_church_count = PipelineContact.query.filter_by(pipeline_id=main_church_pipeline.id).count()
            print(f"Verification: {pipeline_church_count} churches in pipeline {main_church_pipeline.name}")
        
        # Final verification
        final_people_contacts = PipelineContact.query.join(Pipeline).filter(
            Pipeline.is_main_pipeline == True, 
            Pipeline.pipeline_type == "people"
        ).count()
        
        final_church_contacts = PipelineContact.query.join(Pipeline).filter(
            Pipeline.is_main_pipeline == True, 
            Pipeline.pipeline_type == "church"
        ).count()
        
        print(f"\nFinal verification:")
        print(f"Total people added to main pipelines: {total_people_added}")
        print(f"Total churches added to main pipelines: {total_churches_added}")
        print(f"People contacts in database: {final_people_contacts}")
        print(f"Church contacts in database: {final_church_contacts}")
        
        # List all pipeline contacts for debugging
        print("\nAll pipeline contacts in database:")
        all_pipeline_contacts = PipelineContact.query.all()
        print(f"Total pipeline contacts: {len(all_pipeline_contacts)}")
        
        for i, pc in enumerate(all_pipeline_contacts[:10]):  # Show first 10
            pipeline = Pipeline.query.get(pc.pipeline_id)
            stage = PipelineStage.query.get(pc.current_stage_id)
            contact = Contact.query.get(pc.contact_id)
            
            pipeline_name = pipeline.name if pipeline else "Unknown"
            pipeline_type = pipeline.pipeline_type if pipeline else "Unknown"
            stage_name = stage.name if stage else "Unknown"
            contact_name = contact.get_name() if contact else "Unknown"
            contact_type = contact.type if contact else "Unknown"
            
            print(f"  {i+1}. PC ID: {pc.id}, Pipeline: {pipeline_name} ({pipeline_type}), "
                  f"Stage: {stage_name}, Contact: {contact_name} ({contact_type})")

def create_custom_pipelines():
    """Create custom pipelines for each stage of the main pipeline"""
    with app.app_context():
        # Get main pipelines
        main_people_pipelines = Pipeline.query.filter_by(is_main_pipeline=True, pipeline_type="people").all()
        main_church_pipelines = Pipeline.query.filter_by(is_main_pipeline=True, pipeline_type="church").all()
        
        if not main_people_pipelines or not main_church_pipelines:
            print("Main pipelines not found. Please run the setup script first.")
            return
        
        print(f"Creating custom pipelines...")
        
        # Create custom people pipelines
        for main_people_pipeline in main_people_pipelines:
            # Get pipeline stages
            people_stages = PipelineStage.query.filter_by(pipeline_id=main_people_pipeline.id).all()
            
            if not people_stages:
                print(f"No stages found for pipeline {main_people_pipeline.name} (ID: {main_people_pipeline.id})")
                continue
                
            # Create custom people pipelines for each stage
            for stage in people_stages:
                # Check if this custom pipeline already exists
                existing = Pipeline.query.filter_by(
                    name=f"Custom {stage.name} People Pipeline",
                    pipeline_type="people",
                    office_id=main_people_pipeline.office_id
                ).first()
                
                if existing:
                    print(f"Custom pipeline for {stage.name} people already exists.")
                    continue
                
                # Create custom pipeline
                custom_pipeline = Pipeline(
                    name=f"Custom {stage.name} People Pipeline",
                    pipeline_type="people",
                    office_id=main_people_pipeline.office_id,
                    is_main_pipeline=False,
                    description=f"Custom pipeline for {stage.name} people"
                )
                db.session.add(custom_pipeline)
                db.session.flush()  # Get ID without committing
                
                # Create stages
                stage_names = ["Research", "Initial Contact", "Follow-up", "Meeting", "Decision"]
                for i, name in enumerate(stage_names):
                    pipeline_stage = PipelineStage(
                        pipeline_id=custom_pipeline.id,
                        name=name,
                        order=i+1,
                        color=f"#{'%06x' % random.randint(0, 0xFFFFFF)}",  # Random color
                        description=f"{name} stage for {stage.name} people"
                    )
                    db.session.add(pipeline_stage)
                
                # Commit after each custom pipeline is created
                try:
                    db.session.commit()
                    print(f"Created custom pipeline for {stage.name} people.")
                except Exception as e:
                    print(f"Error creating custom pipeline for {stage.name} people: {str(e)}")
                    traceback.print_exc()
                    db.session.rollback()
        
        # Create custom church pipelines
        for main_church_pipeline in main_church_pipelines:
            # Get pipeline stages
            church_stages = PipelineStage.query.filter_by(pipeline_id=main_church_pipeline.id).all()
            
            if not church_stages:
                print(f"No stages found for pipeline {main_church_pipeline.name} (ID: {main_church_pipeline.id})")
                continue
                
            # Create custom church pipelines for each stage
            for stage in church_stages:
                # Check if this custom pipeline already exists
                existing = Pipeline.query.filter_by(
                    name=f"Custom {stage.name} Church Pipeline",
                    pipeline_type="church",
                    office_id=main_church_pipeline.office_id
                ).first()
                
                if existing:
                    print(f"Custom pipeline for {stage.name} churches already exists.")
                    continue
                
                # Create custom pipeline
                custom_pipeline = Pipeline(
                    name=f"Custom {stage.name} Church Pipeline",
                    pipeline_type="church",
                    office_id=main_church_pipeline.office_id,
                    is_main_pipeline=False,
                    description=f"Custom pipeline for {stage.name} churches"
                )
                db.session.add(custom_pipeline)
                db.session.flush()  # Get ID without committing
                
                # Create stages
                stage_names = ["Research", "Initial Contact", "Presentation", "Partnership", "Follow-up"]
                for i, name in enumerate(stage_names):
                    pipeline_stage = PipelineStage(
                        pipeline_id=custom_pipeline.id,
                        name=name,
                        order=i+1,
                        color=f"#{'%06x' % random.randint(0, 0xFFFFFF)}",  # Random color
                        description=f"{name} stage for {stage.name} churches"
                    )
                    db.session.add(pipeline_stage)
                
                # Commit after each custom pipeline is created
                try:
                    db.session.commit()
                    print(f"Created custom pipeline for {stage.name} churches.")
                except Exception as e:
                    print(f"Error creating custom pipeline for {stage.name} churches: {str(e)}")
                    traceback.print_exc()
                    db.session.rollback()
        
        print("Custom pipelines created successfully.")

if __name__ == "__main__":
    # Distribute contacts to main pipelines
    distribute_contacts_to_main_pipelines()
    
    # Create custom pipelines
    create_custom_pipelines()
    
    print("Pipeline population completed successfully.") 