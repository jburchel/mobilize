from app import create_app
from app.models.pipeline import Pipeline
from app.extensions import db

app = create_app()

def fix_pipeline_types():
    """Fix the pipeline types for people pipelines (changing from 'people' to 'person')."""
    with app.app_context():
        # Get all pipelines with type 'people'
        people_pipelines = Pipeline.query.filter_by(pipeline_type='people').all()
        print(f"Found {len(people_pipelines)} pipelines with type 'people'")
        
        # Update the pipeline type to 'person'
        for pipeline in people_pipelines:
            print(f"Changing pipeline '{pipeline.name}' (ID: {pipeline.id}) from 'people' to 'person'")
            pipeline.pipeline_type = 'person'
        
        # Commit the changes
        db.session.commit()
        print("Changes committed to database")
        
        # Verify the changes
        person_pipelines = Pipeline.query.filter_by(pipeline_type='person').all()
        print(f"Now there are {len(person_pipelines)} pipelines with type 'person'")
        
        # Verify no more 'people' pipelines
        people_pipelines = Pipeline.query.filter_by(pipeline_type='people').all()
        print(f"Now there are {len(people_pipelines)} pipelines with type 'people'")

if __name__ == "__main__":
    fix_pipeline_types() 