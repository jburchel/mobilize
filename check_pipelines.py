from app import create_app
from app.models import Pipeline, PipelineStage
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    pipelines = Pipeline.query.all()
    print(f'Found {len(pipelines)} pipelines:')
    for p in pipelines:
        print(f'  ID: {p.id}, Name: {p.name}, Type: {p.pipeline_type}, Is Main: {p.is_main_pipeline}')
        stages = PipelineStage.query.filter_by(pipeline_id=p.id).all()
        print(f'    Stages ({len(stages)}):')
        for s in stages:
            print(f'      - ID: {s.id}, Name: {s.name}, Order: {s.order}')
        
        # Check pipeline contact counts
        contact_count = db.session.execute(
            text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
            {"pipeline_id": p.id}
        ).scalar() or 0
        print(f'    Contact Count (SQL): {contact_count}')
        print(f'    Contact Count (Method): {p.count_contacts()}') 