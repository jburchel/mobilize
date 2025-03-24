"""Template context processors."""
from app.models.pipeline import Pipeline

def register_template_utilities(app):
    """Register template context processors."""
    
    @app.context_processor
    def inject_main_pipelines():
        """Inject main pipelines into all templates."""
        return {
            'people_main_pipeline': Pipeline.get_main_pipeline('people'),
            'church_main_pipeline': Pipeline.get_main_pipeline('church')
        }
        
    @app.context_processor
    def inject_utility_functions():
        """Inject utility functions into all templates."""
        return {
            'pipeline_types': {
                'people': 'People Pipeline',
                'church': 'Church Pipeline'
            }
        } 