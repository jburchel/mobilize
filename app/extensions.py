from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from celery import Celery
from flask_apscheduler import APScheduler
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_caching import Cache
import logging

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
login_manager = LoginManager()
jwt = JWTManager()
csrf = CSRFProtect()
celery = Celery('app')
scheduler = APScheduler()
mail = Mail()  # Initialize Flask-Mail
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()
cache = Cache()

# Configure cache
def configure_cache(app):
    """Configure cache based on app config."""
    cache_config = {
        'CACHE_TYPE': 'SimpleCache',  # Simple in-memory cache
        'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes default timeout
    }
    
    # In production, use Redis if available
    if app.config.get('ENV') == 'production' and app.config.get('REDIS_URL'):
        cache_config.update({
            'CACHE_TYPE': 'RedisCache',
            'CACHE_REDIS_URL': app.config.get('REDIS_URL'),
            'CACHE_DEFAULT_TIMEOUT': 600  # 10 minutes in production
        })
    # For larger development datasets, use filesystem cache
    elif app.config.get('CACHE_TYPE') == 'FileSystemCache':
        import os
        cache_dir = os.path.join(app.instance_path, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        cache_config.update({
            'CACHE_TYPE': 'FileSystemCache',
            'CACHE_DIR': cache_dir,
            'CACHE_THRESHOLD': 1000  # Maximum number of items the cache will store
        })
        
    # Apply configuration
    app.config.update(cache_config)
    cache.init_app(app)

# Create base model class
Base = db.Model

# Mail stub for development/testing environments
class MailStub:
    logger = logging.getLogger('mail_stub')
    
    def send(self, message):
        """Log the message instead of sending it"""
        recipients = ', '.join(message.recipients)
        self.logger.info(f"EMAIL WOULD BE SENT - To: {recipients}, Subject: {message.subject}")
        return True

# Note: We'll conditionally use either mail or MailStub() in app/__init__.py based on config 