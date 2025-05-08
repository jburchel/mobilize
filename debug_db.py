from app import create_app
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.person import Person
from app.models.church import Church
from app.extensions import db

app = create_app()

with app.app_context():
    print("\n===== CHECKING DATABASE FOR PIPELINE DATA =====\n")
    
    # Get all people and churches
    people_count = Person.query.count()
    church_count = Church.query.count()
    print(f"Total people in database: {people_count}")
    print(f"Total churches in database: {church_count}")
    
    # Get all pipelines
    pipelines = Pipeline.query.all()
    print(f"\nTotal pipelines: {len(pipelines)}")
    
    # Find main pipelines
    main_pipelines = Pipeline.query.filter_by(is_main_pipeline=True).all()
    print(f"Main pipelines: {len(main_pipelines)}")
    
    for pipeline in main_pipelines:
        print(f"\nPipeline: {pipeline.id} - {pipeline.name} ({pipeline.pipeline_type})")
        
        # Get stages for this pipeline
        stages = PipelineStage.query.filter_by(pipeline_id=pipeline.id).order_by(PipelineStage.order).all()
        print(f"Stages: {len(stages)}")
        
        for stage in stages:
            print(f"  - Stage: {stage.id} - {stage.name} (order: {stage.order})")
            
            # Count contacts in this stage
            if pipeline.pipeline_type in ['person', 'people']:
                contacts = db.session.query(PipelineContact).join(
                    Person, Person.id == PipelineContact.contact_id
                ).filter(
                    PipelineContact.pipeline_id == pipeline.id,
                    PipelineContact.current_stage_id == stage.id
                ).all()
                
                print(f"    * People in this stage: {len(contacts)}")
                for contact in contacts:
                    person = Person.query.get(contact.contact_id)
                    if person:
                        print(f"      - {person.first_name} {person.last_name} (ID: {person.id})")
            else:
                contacts = db.session.query(PipelineContact).join(
                    Church, Church.id == PipelineContact.contact_id
                ).filter(
                    PipelineContact.pipeline_id == pipeline.id,
                    PipelineContact.current_stage_id == stage.id
                ).all()
                
                print(f"    * Churches in this stage: {len(contacts)}")
                for contact in contacts:
                    church = Church.query.get(contact.contact_id)
                    if church:
                        print(f"      - {church.name} (ID: {church.id})")
    
    # Check if people are in pipelines
    print("\n===== CHECKING PEOPLE IN PIPELINES =====\n")
    people_in_pipelines = db.session.query(PipelineContact).join(
        Person, Person.id == PipelineContact.contact_id
    ).count()
    print(f"People in pipelines: {people_in_pipelines}")
    
    # Check if churches are in pipelines
    print("\n===== CHECKING CHURCHES IN PIPELINES =====\n")
    churches_in_pipelines = db.session.query(PipelineContact).join(
        Church, Church.id == PipelineContact.contact_id
    ).count()
    print(f"Churches in pipelines: {churches_in_pipelines}")
    
    # Check if we need to add people to pipelines
    if people_count > 0 and people_in_pipelines == 0:
        print("\n===== PEOPLE NEED TO BE ADDED TO PIPELINES =====\n")
        
        # Find the main people pipeline
        people_pipeline = Pipeline.query.filter(
            Pipeline.is_main_pipeline,
            Pipeline.pipeline_type.in_(['person', 'people'])
        ).first()
        
        if people_pipeline:
            print(f"Found main people pipeline: {people_pipeline.id} - {people_pipeline.name}")
            
            # Find the first stage (usually Promotion)
            first_stage = PipelineStage.query.filter_by(
                pipeline_id=people_pipeline.id
            ).order_by(PipelineStage.order).first()
            
            if first_stage:
                print(f"Found first stage: {first_stage.id} - {first_stage.name}")
                
                # Check how many people need to be added
                people_to_add = Person.query.all()
                print(f"People to add to pipeline: {len(people_to_add)}")
    
    # Check if we need to add churches to pipelines
    if church_count > 0 and churches_in_pipelines == 0:
        print("\n===== CHURCHES NEED TO BE ADDED TO PIPELINES =====\n")
        
        # Find the main church pipeline
        church_pipeline = Pipeline.query.filter(
            Pipeline.is_main_pipeline,
            Pipeline.pipeline_type == 'church'
        ).first()
        
        if church_pipeline:
            print(f"Found main church pipeline: {church_pipeline.id} - {church_pipeline.name}")
            
            # Find the first stage (usually Promotion)
            first_stage = PipelineStage.query.filter_by(
                pipeline_id=church_pipeline.id
            ).order_by(PipelineStage.order).first()
            
            if first_stage:
                print(f"Found first stage: {first_stage.id} - {first_stage.name}")
                
                # Check how many churches need to be added
                churches_to_add = Church.query.all()
                print(f"Churches to add to pipeline: {len(churches_to_add)}")
