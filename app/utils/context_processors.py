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
        
        def get_badge_color_for_pipeline(stage):
            """Get the appropriate badge color for a pipeline stage."""
            if not stage:
                return 'secondary'
            
            stage = stage.upper()
            if stage == 'PROMOTION':
                return 'info'
            elif stage == 'INFORMATION':
                return 'primary'
            elif stage == 'INVITATION':
                return 'warning'
            elif stage == 'CONFIRMATION':
                return 'success'
            elif stage == 'AUTOMATION':
                return 'danger'
            elif stage == 'EN42':
                return 'dark'
            else:
                return 'secondary'
        
        def get_badge_color_for_priority(priority):
            """Get the appropriate badge color for a priority level."""
            if not priority:
                return 'secondary'
                
            priority = priority.lower()
            if 'high' in priority or 'urgent' in priority:
                return 'danger'
            elif 'medium' in priority:
                return 'warning'
            elif 'low' in priority:
                return 'info'
            else:
                return 'secondary'
        
        return {
            'pipeline_types': {
                'people': 'People Pipeline',
                'church': 'Church Pipeline'
            },
            'get_badge_color_for_pipeline': get_badge_color_for_pipeline,
            'get_badge_color_for_priority': get_badge_color_for_priority
        } 