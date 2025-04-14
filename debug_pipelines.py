"""
Debugging script for pipelines.
Run with: python debug_pipelines.py
"""
from app import create_app
from app.models.pipeline import Pipeline

app = create_app()

with app.app_context():
    # Check main people pipeline
    people_pipeline = Pipeline.query.filter_by(
        is_main_pipeline=True, 
        pipeline_type='person'
    ).first()
    
    if not people_pipeline:
        people_pipeline = Pipeline.query.filter_by(
            is_main_pipeline=True, 
            pipeline_type='people'
        ).first()
    
    # Check main church pipeline
    church_pipeline = Pipeline.query.filter_by(
        is_main_pipeline=True, 
        pipeline_type='church'
    ).first()
    
    print("People Pipeline:")
    if people_pipeline:
        print(f"- ID: {people_pipeline.id}")
        print(f"- Name: {people_pipeline.name}")
        print(f"- Type: {people_pipeline.pipeline_type}")
    else:
        print("None found")
    
    print("\nChurch Pipeline:")
    if church_pipeline:
        print(f"- ID: {church_pipeline.id}")
        print(f"- Name: {church_pipeline.name}")
        print(f"- Type: {church_pipeline.pipeline_type}")
    else:
        print("None found")
    
    # List all pipelines
    print("\nAll Pipelines:")
    pipelines = Pipeline.query.all()
    for p in pipelines:
        print(f"- ID: {p.id}, Name: {p.name}, Type: {p.pipeline_type}, Main: {p.is_main_pipeline}") 