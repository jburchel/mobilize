#!/bin/bash

# Script to run pipeline automations
# Add this to crontab to run regularly:
# 0 2 * * * /path/to/your/app/scripts/run_automations.sh >> /path/to/your/app/logs/automations.log 2>&1

# Set working directory to app root
cd "$(dirname "$0")/.."

# Activate Python virtual environment if using one
# source /path/to/venv/bin/activate

# Set Flask environment variables
export FLASK_APP=app/app.py
export FLASK_ENV=production

# Run the automations command
echo "--- $(date) - Running pipeline automations ---"
flask run-automations
echo "--- $(date) - Finished pipeline automations ---" 