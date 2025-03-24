from app import create_app
from app.models.pipeline import Pipeline

app = create_app()
with app.app_context():
    print('Main Pipelines:')
    for p in Pipeline.query.filter_by(is_main_pipeline=True).all():
        print(f'{p.id}: {p.name}, Type: {p.pipeline_type}')
    
    print('\nAll Pipelines and Their Stages:')
    for p in Pipeline.query.all():
        print(f'Pipeline {p.id}: {p.name}')
        for s in p.stages.all():
            print(f'  - Stage {s.id}: {s.name}')
