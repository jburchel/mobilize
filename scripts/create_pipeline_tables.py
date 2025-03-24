"""
Script to create pipeline tables in the database.
"""
from app import create_app
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact, PipelineStageHistory
from app.extensions import db

def main():
    """Create pipeline tables."""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Pipeline tables created successfully.")

if __name__ == "__main__":
    main() 