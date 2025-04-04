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

# Configure cache
def configure_cache(app):
    """Configure cache based on app config."""
    pass  # Implementation details will be added later

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