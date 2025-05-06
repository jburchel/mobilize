from flask import flash, redirect, url_for
from app.models.pipeline import Pipeline

class PipelineGuard:
    """
    Guard class to protect main pipelines from being modified through the UI.
    Only code changes should be able to modify main pipelines.
    """
    
    @staticmethod
    def can_modify_pipeline(pipeline_id):
        """
        Check if the current user can modify the pipeline.
        Main pipelines cannot be modified through the UI at all.
        
        Returns:
            tuple: (can_modify, redirect_response or None)
        """
        # Get the pipeline
        pipeline = Pipeline.query.get(pipeline_id)
        
        # If pipeline doesn't exist, can't modify it
        if not pipeline:
            return False, redirect(url_for('pipelines.index'))
        
        # Main pipelines cannot be modified through the UI at all
        if pipeline.is_main_pipeline:
            flash('Main pipelines cannot be modified through the UI. These pipelines are system-defined.', 'danger')
            return False, redirect(url_for('pipelines.index'))
        
        # All other pipelines can be modified by appropriate users
        return True, None
    
    @staticmethod
    def can_delete_pipeline(pipeline_id):
        """
        Check if the current user can delete the pipeline.
        Main pipelines cannot be deleted through the UI at all.
        
        Returns:
            tuple: (can_delete, redirect_response or None)
        """
        # Get the pipeline
        pipeline = Pipeline.query.get(pipeline_id)
        
        # If pipeline doesn't exist, can't delete it
        if not pipeline:
            return False, redirect(url_for('pipelines.index'))
        
        # Main pipelines cannot be deleted
        if pipeline.is_main_pipeline:
            flash('Main pipelines cannot be deleted. These pipelines are system-defined.', 'danger')
            return False, redirect(url_for('pipelines.index'))
        
        # All other pipelines can be deleted by appropriate users
        return True, None
