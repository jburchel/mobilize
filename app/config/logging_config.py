import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(app):
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Set the basic logging level from environment variable
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    # Create formatters
    verbose_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure the Flask app logger
    app.logger.setLevel(numeric_level)
    
    # Always log errors to file
    error_file_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(verbose_formatter)
    app.logger.addHandler(error_file_handler)
    
    # Log to stdout if configured
    if os.getenv('LOG_TO_STDOUT', 'False').lower() == 'true':
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(numeric_level)
        stream_handler.setFormatter(simple_formatter)
        app.logger.addHandler(stream_handler)
    
    # Development logging to file
    if app.debug:
        debug_file_handler = RotatingFileHandler(
            'logs/debug.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        debug_file_handler.setLevel(logging.DEBUG)
        debug_file_handler.setFormatter(verbose_formatter)
        app.logger.addHandler(debug_file_handler)
    
    # First log message
    app.logger.info('Logging setup completed') 