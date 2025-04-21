#!/bin/bash
set -e

# Startup script for the Mobilize CRM app

# Print Python and environment information
echo "Python version:"
python --version
echo

echo "Environment variables:"
echo "FLASK_APP: $FLASK_APP"
echo "FLASK_ENV: $FLASK_ENV"
echo "DATABASE_URL is set: $(if [ -n "$DATABASE_URL" ]; then echo "Yes"; else echo "No"; fi)"
echo "SECRET_KEY is set: $(if [ -n "$SECRET_KEY" ]; then echo "Yes"; else echo "No"; fi)"
echo

# Run test script to verify imports
echo "Running import test script..."
python test_app_imports.py || echo "Import test failed, but continuing startup"
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