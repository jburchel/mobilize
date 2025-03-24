from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from celery import Celery
from flask_apscheduler import APScheduler

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
login_manager = LoginManager()
jwt = JWTManager()
csrf = CSRFProtect()
celery = Celery('app')
scheduler = APScheduler()

# Create base model class
Base = db.Model 