from app import create_app
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.person import Person
from app.models.church import Church
from app.extensions import db

app = create_app()

def check_pipelines():
    """Print detailed information about all pipelines in the database."""
    with app.app_context():
        # Get all pipelines
        pipelines = Pipeline.query.all()
        print(f"Found {len(pipelines)} pipelines:")
        
        for pipeline in pipelines:
            print(f"\nPipeline ID: {pipeline.id}")
            print(f"  Name: {pipeline.name}")
            print(f"  Type: {pipeline.pipeline_type}")
            print(f"  Office ID: {pipeline.office_id}")
            print(f"  Main Pipeline: {pipeline.is_main_pipeline}")
            
            # Get stages for this pipeline
            stages = PipelineStage.query.filter_by(pipeline_id=pipeline.id).order_by(PipelineStage.order).all()
            print(f"  Stages ({len(stages)}):")
            for stage in stages:
                print(f"    - {stage.name} (ID: {stage.id}, Order: {stage.order})")
            
            # Get contacts for this pipeline
            contacts = PipelineContact.query.filter_by(pipeline_id=pipeline.id).all()
            print(f"  Contacts: {len(contacts)}")
            
            if pipeline.pipeline_type == 'person':
                # For people pipelines, get the name of some contacts
                if contacts:
                    print("    Sample people in pipeline:")
                    for contact in contacts[:5]:  # Just show the first 5
                        person = Person.query.get(contact.contact_id)
                        if person:
                            print(f"      - {person.first_name} {person.last_name} (ID: {person.id})")
                else:
                    print("    No people in this pipeline")
            
            if pipeline.pipeline_type == 'church':
                # For church pipelines, get the name of some contacts
                if contacts:
                    print("    Sample churches in pipeline:")
                    for contact in contacts[:5]:  # Just show the first 5
                        church = Church.query.get(contact.contact_id)
                        if church:
                            print(f"      - {church.name} (ID: {church.id})")
                else:
                    print("    No churches in this pipeline")
        
        # Print summary counts
        total_contacts = PipelineContact.query.count()
        total_people = Person.query.count()
        total_churches = Church.query.count()
        
        print("\nSummary:")
        print(f"  Total Pipeline Contacts: {total_contacts}")
        print(f"  Total People: {total_people}")
        print(f"  Total Churches: {total_churches}")
        
        # Check for person type pipelines
        person_pipelines = Pipeline.query.filter_by(pipeline_type='person').all()
        print(f"\nPerson pipelines: {len(person_pipelines)}")
        
        # Check for people type pipelines
        people_pipelines = Pipeline.query.filter_by(pipeline_type='people').all()
        print(f"People pipelines: {len(people_pipelines)}")
        
        # Count main pipelines
        main_pipelines = Pipeline.query.filter_by(is_main_pipeline=True).all()
        print(f"Main pipelines: {len(main_pipelines)}")
        for p in main_pipelines:
            print(f"  - {p.name} (Type: {p.pipeline_type}, Office: {p.office_id})")

if __name__ == "__main__":
    check_pipelines() 