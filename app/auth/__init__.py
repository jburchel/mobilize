from app.auth.firebase import init_firebase
from app.auth.routes import auth_bp
from flask_jwt_extended import create_access_token as jwt_create_access_token

# ... existing code ... 

def create_access_token(user_data):
    """Create a JWT access token for the given user data."""
    return jwt_create_access_token(identity=user_data) 