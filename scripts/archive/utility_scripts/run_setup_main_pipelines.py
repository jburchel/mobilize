from app import create_app
from app.utils.setup_main_pipelines import setup_main_pipelines

app = create_app()
with app.app_context():
    setup_main_pipelines()
    print('setup_main_pipelines() complete') 