from flask import Blueprint

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Import the actual routes from the auth directory - must be after Blueprint creation
from app.auth.routes import *
