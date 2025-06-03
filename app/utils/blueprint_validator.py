"""
Utility for validating and safely registering Flask blueprints.
"""

from flask import Flask, Blueprint, current_app
import logging

def get_registered_blueprint_names(app):
    """Get a list of all registered blueprint names in the app."""
    return [bp.name for bp in app.blueprints.values()]

def is_blueprint_registered(app, name):
    """Check if a blueprint with the given name is already registered."""
    return name in app.blueprints

def generate_unique_name(base_name, prefix=""):
    """Generate a unique blueprint name based on the base name and prefix."""
    if not prefix:
        return base_name
        
    # Clean the prefix to create a valid Python identifier
    clean_prefix = prefix.replace('/', '_').strip('_')
    if clean_prefix:
        return f"{base_name}_{clean_prefix}"
    return base_name

def safe_register_blueprint(app, blueprint, url_prefix=None, **kwargs):
    """
    Safely register a blueprint with the Flask app, ensuring a unique name.
    
    Args:
        app: Flask application instance
        blueprint: Blueprint to register
        url_prefix: URL prefix for the blueprint
        **kwargs: Additional arguments to pass to register_blueprint
    
    Returns:
        bool: True if registration was successful, False otherwise
    """
    original_name = blueprint.name
    
    # If name is explicitly provided in kwargs, use that
    if 'name' in kwargs:
        try:
            app.register_blueprint(blueprint, url_prefix=url_prefix, **kwargs)
            app.logger.info(f"Registered blueprint '{original_name}' with custom name '{kwargs['name']}'")
            return True
        except ValueError as e:
            app.logger.warning(f"Failed to register blueprint with custom name: {str(e)}")
            # Continue to auto-naming
    
    # Try with auto-generated name
    unique_name = generate_unique_name(original_name, url_prefix)
    
    # If the auto-generated name is already taken, add a timestamp
    if is_blueprint_registered(app, unique_name):
        import time
        unique_name = f"{original_name}_{int(time.time())}"
    
    try:
        kwargs['name'] = unique_name
        app.register_blueprint(blueprint, url_prefix=url_prefix, **kwargs)
        app.logger.info(f"Registered blueprint '{original_name}' with generated name '{unique_name}'")
        return True
    except Exception as e:
        app.logger.error(f"Failed to register blueprint '{original_name}': {str(e)}")
        return False