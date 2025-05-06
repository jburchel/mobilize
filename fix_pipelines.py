from app import create_app, db
from app.models.pipeline import Pipeline, PipelineStage

app = create_app()

with app.app_context():
    # Identify the duplicate pipeline (ID: 5)
    duplicate_pipeline = Pipeline.query.get(5)
    
    if duplicate_pipeline:
        print(f"Found duplicate pipeline: ID {duplicate_pipeline.id}, Name: {duplicate_pipeline.name}")
        
        # Get all stages for this pipeline
        stages = PipelineStage.query.filter_by(pipeline_id=duplicate_pipeline.id).all()
        print(f"Found {len(stages)} stages for the duplicate pipeline")
        
        # Delete all stages first (due to foreign key constraints)
        for stage in stages:
            print(f"Deleting stage: ID {stage.id}, Name: {stage.name}")
            db.session.delete(stage)
        
        # Delete the duplicate pipeline
        print(f"Deleting duplicate pipeline: ID {duplicate_pipeline.id}")
        db.session.delete(duplicate_pipeline)
        
        # Commit the changes
        db.session.commit()
        print("Changes committed successfully")
        
        # Verify the changes
        pipeline_count = Pipeline.query.count()
        stage_count = PipelineStage.query.count()
        print(f"\nAfter cleanup: {pipeline_count} pipelines and {stage_count} pipeline stages")
    else:
        print("Duplicate pipeline not found")
