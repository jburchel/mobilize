import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_logs():
    try:
        logger.info("Checking logs for Mobilize-CRM on Google Cloud Run...")

        # Ensure we're in the correct directory
        os.chdir('/Users/jimburchel/Developer-Playground/mobilize-app')

        # Run gcloud command to fetch logs
        logs_command = 'gcloud logging read "resource.type=cloud_run_revision AND logName:/logs/stdout AND resource.labels.service_name=mobilize-crm" --limit 50 --format "value(textPayload)"'
        process = subprocess.run(logs_command, shell=True, check=True, text=True, capture_output=True)
        logs = process.stdout.strip()
        logger.info(f"Recent logs:\n{logs}")

        # Check for errors in logs
        if 'error' in logs.lower() or 'exception' in logs.lower():
            logger.warning("Potential errors found in logs. Please review for specific issues.")
        else:
            logger.info("No obvious errors found in recent logs.")

        logger.info("Successfully checked logs.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking logs: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error checking logs: {str(e)}")

if __name__ == "__main__":
    check_logs()
