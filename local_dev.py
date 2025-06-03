from app import create_app
import os

# Set development environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['DATABASE_URL'] = 'sqlite:///mobilize.db'
os.environ['SECRET_KEY'] = 'dev-secret-key'
os.environ['CSRF_ENABLED'] = 'True'

# Create the app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
