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
            
            stage = stage.lower()
            if 'lead' in stage or 'new' in stage:
                return 'info'
            elif 'contact' in stage or 'follow' in stage:
                return 'primary'
            elif 'qualified' in stage or 'meeting' in stage:
                return 'success'
            elif 'proposal' in stage or 'negotiation' in stage:
                return 'warning'
            elif 'closed' in stage and 'won' in stage:
                return 'success'
            elif 'closed' in stage and 'lost' in stage:
                return 'danger'
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