#!/usr/bin/env python3
"""
Script to check pipelines and contacts
"""
from app import create_app, db
from app.models import Pipeline, PipelineStage, PipelineContact, Contact, Person, Church, Office
from sqlalchemy import text
import sys

app = create_app()

def check_pipelines():
    """Check pipeline data"""
    with app.app_context():
        # Office assignments
        print("OFFICE ASSIGNMENTS:")
        offices = Office.query.all()
        print(f"Found {len(offices)} offices:")
        for office in offices:
            people_count = Person.query.filter_by(office_id=office.id).count()
            church_count = Church.query.filter_by(office_id=office.id).count()
            print(f"  Office: {office.name} (ID: {office.id})")
            print(f"    People assigned: {people_count}")
            print(f"    Churches assigned: {church_count}")
        
        print()
        # People without office
        people_without_office = Person.query.filter_by(office_id=None).all()
        print("People without office:")
        print(f"  Count: {len(people_without_office)}")
        
        # Churches without office
        churches_without_office = Church.query.filter_by(office_id=None).all()
        print("Churches without office:")
        print(f"  Count: {len(churches_without_office)}")
        
        print()
        # Get main pipelines
        main_pipelines = Pipeline.query.filter_by(is_main_pipeline=True).all()
        print(f"Found {len(main_pipelines)} main pipelines:")
        
        # Check contacts for each main pipeline
        for pipeline in main_pipelines:
            print(f"  Pipeline: {pipeline.name} (ID: {pipeline.id})")
            print(f"    Type: {pipeline.pipeline_type}")
            print(f"    Office ID: {pipeline.office_id}")
            
            # Get pipeline stages
            stages = PipelineStage.query.filter_by(pipeline_id=pipeline.id).all()
            print(f"    Stages: {len(stages)}")
            
            # Direct SQL query for pipeline_contacts for this pipeline
            result = db.session.execute(text(f"SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = {pipeline.id}")).first()
            pc_count = result[0] if result else 0
            print(f"    Pipeline Contacts (SQL): {pc_count}")
            
            # Pipeline contacts via ORM
            pipeline_contacts = PipelineContact.query.filter_by(pipeline_id=pipeline.id).all()
            print(f"    Pipeline Contacts (ORM): {len(pipeline_contacts)}")
            
            # Check contacts
            if pipeline.pipeline_type == 'people':
                actual_people = db.session.execute(text(f"""
                    SELECT c.id, c.type, p.first_name, p.last_name 
                    FROM contacts c
                    JOIN people p ON c.id = p.id
                    JOIN pipeline_contacts pc ON c.id = pc.contact_id
                    WHERE pc.pipeline_id = {pipeline.id}
                """)).fetchall()
                print(f"    Actual people: {len(actual_people)}")
                
                # Show first 5 people in this pipeline
                if actual_people:
                    print(f"    First 5 people in pipeline:")
                    for i, person in enumerate(actual_people[:5]):
                        print(f"      {i+1}. {person.first_name} {person.last_name}")
                
                # Stage distribution
                print(f"    Stage distribution:")
                for stage in stages:
                    stage_count = db.session.execute(text(f"""
                        SELECT COUNT(*) FROM pipeline_contacts 
                        WHERE pipeline_id = {pipeline.id} AND current_stage_id = {stage.id}
                    """)).scalar()
                    print(f"      {stage.name}: {stage_count}")
            else:
                actual_churches = db.session.execute(text(f"""
                    SELECT c.id, c.type, ch.name 
                    FROM contacts c
                    JOIN churches ch ON c.id = ch.id
                    JOIN pipeline_contacts pc ON c.id = pc.contact_id
                    WHERE pc.pipeline_id = {pipeline.id}
                """)).fetchall()
                print(f"    Actual churches: {len(actual_churches)}")
                
                # Show first 5 churches in this pipeline
                if actual_churches:
                    print(f"    First 5 churches in pipeline:")
                    for i, church in enumerate(actual_churches[:5]):
                        print(f"      {i+1}. {church.name}")
                
                # Stage distribution
                print(f"    Stage distribution:")
                for stage in stages:
                    stage_count = db.session.execute(text(f"""
                        SELECT COUNT(*) FROM pipeline_contacts 
                        WHERE pipeline_id = {pipeline.id} AND current_stage_id = {stage.id}
                    """)).scalar()
                    print(f"      {stage.name}: {stage_count}")
            
            print("\n")
        
        # Get counts for overall stats
        total_people = Person.query.count()
        total_churches = Church.query.count()
        total_contacts = Contact.query.count()
        total_pipeline_contacts = db.session.execute(text("SELECT COUNT(*) FROM pipeline_contacts")).scalar()
        total_pipelines = Pipeline.query.count()
        total_stages = PipelineStage.query.count()
        
        # Check all pipeline contacts
        print("ALL PIPELINE CONTACTS:")
        print(f"Total pipeline contacts in database: {total_pipeline_contacts}")
        print()
        
        print("Sample pipeline contacts:")
        pipeline_contacts = PipelineContact.query.limit(10).all()
        for i, pc in enumerate(pipeline_contacts):
            pipeline = Pipeline.query.get(pc.pipeline_id)
            stage = PipelineStage.query.get(pc.current_stage_id)
            contact = Contact.query.get(pc.contact_id)
            
            pipeline_name = pipeline.name if pipeline else "Unknown"
            stage_name = stage.name if stage else "Unknown"
            contact_name = contact.get_name() if contact else "Unknown"
            contact_type = contact.type if contact else "Unknown"
            
            print(f"  {i+1}. PC ID: {pc.id}, Pipeline: {pipeline_name}, Stage: {stage_name}, Contact: {contact_name} ({contact_type})")
        
        print()
        print("OVERALL COUNTS:")
        print(f"Total People: {total_people}")
        print(f"Total Churches: {total_churches}")
        print(f"Total Contacts: {total_contacts}")
        print(f"Total Pipeline Contacts: {total_pipeline_contacts}")
        print(f"Total Pipelines: {total_pipelines}")
        print(f"Total Stages: {total_stages}")
        
        # Direct SQL query for pipeline contacts
        print("\nDIRECT DATABASE QUERY FOR PIPELINE CONTACTS:")
        sql_count = db.session.execute(text("SELECT COUNT(*) FROM pipeline_contacts")).scalar()
        print(f"Direct SQL count of pipeline_contacts: {sql_count}")
        
        # Get detailed info about all pipeline contacts
        print("\nDETAILED PIPELINE CONTACT INFO (DIRECT SQL):")
        pipeline_contacts_data = db.session.execute(text("""
            SELECT 
                pc.id as pc_id, 
                pc.pipeline_id, 
                pc.contact_id, 
                pc.current_stage_id,
                p.name as pipeline_name, 
                p.pipeline_type,
                p.is_main_pipeline,
                ps.name as stage_name,
                c.type as contact_type,
                CASE 
                    WHEN c.type = 'person' THEN (SELECT first_name || ' ' || last_name FROM people WHERE id = pc.contact_id)
                    WHEN c.type = 'church' THEN (SELECT name FROM churches WHERE id = pc.contact_id)
                    ELSE 'Unknown'
                END as contact_name
            FROM pipeline_contacts pc
            JOIN pipelines p ON pc.pipeline_id = p.id
            JOIN pipeline_stages ps ON pc.current_stage_id = ps.id
            JOIN contacts c ON pc.contact_id = c.id
        """)).fetchall()
        
        print(f"Found {len(pipeline_contacts_data)} pipeline contacts via direct SQL query:")
        for i, pc in enumerate(pipeline_contacts_data):
            print(f"  {i+1}. PC ID: {pc.pc_id}")
            print(f"     Pipeline: {pc.pipeline_name} (ID: {pc.pipeline_id}, Type: {pc.pipeline_type}, Main: {pc.is_main_pipeline})")
            print(f"     Stage: {pc.stage_name} (ID: {pc.current_stage_id})")
            print(f"     Contact: {pc.contact_name} (ID: {pc.contact_id}, Type: {pc.contact_type})")
            print()
        
        # List all pipelines with contact counts
        print("ALL PIPELINES:")
        all_pipelines = db.session.execute(text("""
            SELECT p.id, p.name, p.pipeline_type, p.is_main_pipeline, p.office_id,
                  (SELECT COUNT(*) FROM pipeline_contacts pc WHERE pc.pipeline_id = p.id) as contact_count
            FROM pipelines p
            ORDER BY p.id
        """)).fetchall()
        
        for i, p in enumerate(all_pipelines):
            print(f"  {i+1}. ID: {p.id}, Name: {p.name}, Type: {p.pipeline_type}, Main: {p.is_main_pipeline}, Office: {p.office_id}, Contacts: {p.contact_count}")
        
        # Force a vacuum to ensure database is consistent
        db.session.execute(text("VACUUM"))
        db.session.commit()

if __name__ == "__main__":
    check_pipelines()
    sys.exit(0)
