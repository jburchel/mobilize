from app import create_app
from app.models import Pipeline, PipelineContact

app = create_app()
with app.app_context():
    p = Pipeline.query.filter_by(is_main_pipeline=True, pipeline_type='person').first()
    print('Main People Pipeline ID:', p.id if p else None)
    print('Contacts in pipeline:', PipelineContact.query.filter_by(pipeline_id=p.id).count() if p else None) 