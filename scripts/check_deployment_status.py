import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_deployment_status():
    try:
        logger.info("Checking deployment status on Google Cloud Run...")

        # Ensure we're in the correct directory
        os.chdir('/Users/jimburchel/Developer-Playground/mobilize-app')

        # Run gcloud command to check status
        status_command = 'gcloud run services describe mobilize-crm --region us-central1 --format "value(status.conditions[0].message)"'
        process = subprocess.run(status_command, shell=True, check=True, text=True, capture_output=True)
        status_message = process.stdout.strip()
        logger.info(f"Deployment status: {status_message}")

        if 'Ready' in status_message:
            logger.info("Deployment is ready and operational.")
        else:
            logger.warning("Deployment is not yet ready. Please check again later or review logs for issues.")

        # Additional check for URL to access the service
        url_command = 'gcloud run services describe mobilize-crm --region us-central1 --format "value(status.address.url)"'
        url_process = subprocess.run(url_command, shell=True, check=True, text=True, capture_output=True)
        url = url_process.stdout.strip()
        logger.info(f"Service URL: {url}")

        logger.info("Successfully checked deployment status.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking deployment status: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error checking deployment status: {str(e)}")

if __name__ == "__main__":
    check_deployment_status()
