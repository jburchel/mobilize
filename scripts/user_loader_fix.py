import os
from dotenv import load_dotenv
from app import create_app
from app.models.user import User
from app.extensions import login_manager
from flask_login import LoginManager

# Load environment variables
load_dotenv('.env.development')

# Create app instance
app = create_app()

# Enable development mode
app.config['DEVELOPMENT'] = True
app.config['FLASK_ENV'] = 'development'

# Print some debug info
print(f"Google Client ID: {os.getenv('GOOGLE_CLIENT_ID')}")
print(f"Server Name: {app.config.get('SERVER_NAME')}")

# Register user_loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(debug=True, port=8080) 