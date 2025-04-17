#!/bin/bash

# Find any processes running on port 8000 and kill them
echo "Looking for processes running on port 8000..."
PORT_PIDS=$(lsof -i :8000 -t)

if [ -n "$PORT_PIDS" ]; then
    echo "Found processes running on port 8000, killing them: $PORT_PIDS"
    kill -9 $PORT_PIDS
    echo "Killed processes on port 8000"
else
    echo "No processes found running on port 8000"
fi

# Get the absolute path of the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the absolute path of the project directory (parent of the script directory)
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to the project directory
cd "$PROJECT_DIR"

# Determine the virtual environment directory
if [ -d "venv" ]; then
    VENV_DIR="venv"
elif [ -d "venv_py312" ]; then
    VENV_DIR="venv_py312"
else
    echo "No virtual environment directory found. Please create one first."
    exit 1
fi

# Activate the virtual environment and run the app
echo "Activating virtual environment from $VENV_DIR..."
source "$VENV_DIR/bin/activate"

echo "Starting the app on port 8000..."
FLASK_APP=app.py flask run --host=0.0.0.0 --port=8000 