#!/bin/bash
set -e

# Startup script for the Mobilize CRM app

# Print Python and environment information
echo "Python version:"
python3 --version
echo

echo "Environment variables:"
echo "FLASK_APP: $FLASK_APP"
echo "FLASK_ENV: $FLASK_ENV"
echo "DATABASE_URL is set: $(if [ -n "$DATABASE_URL" ]; then echo "Yes"; else echo "No"; fi)"
echo "SECRET_KEY is set: $(if [ -n "$SECRET_KEY" ]; then echo "Yes"; else echo "No"; fi)"
echo "FIREBASE_PROJECT_ID is set: $(if [ -n "$FIREBASE_PROJECT_ID" ]; then echo "Yes"; else echo "No"; fi)"
echo

# Create Firebase test script
echo "Creating Firebase test script..."
cat > test_firebase.py << EOL
import os
import firebase_admin
from firebase_admin import credentials

def test_firebase():
    print("Testing Firebase initialization...")
    
    project_id = os.environ.get('FIREBASE_PROJECT_ID')
    if not project_id:
        print("ERROR: FIREBASE_PROJECT_ID environment variable is not set!")
        return False
        
    try:
        # Create credential
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id,
            "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\\n'),
            "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.environ.get('FIREBASE_CLIENT_CERT_URL')
        })
        
        # Initialize app
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully!")
        return True
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        return False

if __name__ == "__main__":
    test_firebase()
EOL

# Test Firebase initialization separately
echo "Testing Firebase initialization..."
python3 test_firebase.py || echo "Firebase initialization test failed, but continuing startup"
echo

# Run test script to verify imports
echo "Running import test script..."
python3 test_app_imports.py || echo "Import test failed, but continuing startup"
echo

# Check app structure
echo "Checking app structure..."
if [ -f app.py ]; then
    echo "✅ app.py file exists"
    echo "Content of app.py:"
    cat app.py
    echo
else
    echo "❌ app.py file does not exist"
fi

# Check for app package
if [ -d app ]; then
    echo "✅ app directory exists"
    echo "Files in app directory:"
    ls -la app/
    echo
    
    echo "Checking for __init__.py:"
    if [ -f app/__init__.py ]; then
        echo "✅ app/__init__.py exists"
        echo "First 10 lines of app/__init__.py:"
        head -n 10 app/__init__.py
        echo "..."
        echo "Lines containing 'create_app':"
        grep -n "create_app" app/__init__.py || echo "No create_app function found"
        echo
    else
        echo "❌ app/__init__.py does not exist"
    fi
else
    echo "❌ app directory does not exist"
fi

# Print script environment info
echo "Startup script executed by: $(whoami)"
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la
echo

# Start the application
echo "Starting application with gunicorn..."
exec gunicorn --config=gunicorn.conf.py "app:create_app()" 