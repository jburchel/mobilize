import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def deploy_to_gcloud():
    try:
        logger.info("Starting deployment to Google Cloud Run...")

        # Ensure we're in the correct directory
        os.chdir('/Users/jimburchel/Developer-Playground/mobilize-app')

        # Check if communications_simple.py exists, if not, restore it
        simple_comm_path = 'app/routes/communications_simple.py'
        if not os.path.exists(simple_comm_path):
            logger.warning("communications_simple.py not found, restoring...")
            restore_command = 'python3 scripts/restore_communications_files.py'
            restore_process = subprocess.run(restore_command, shell=True, check=True, text=True, capture_output=True)
            logger.info(f"Restore output: {restore_process.stdout}")

        # Run gcloud deploy command
        deploy_command = 'gcloud run deploy mobilize-crm --source . --region us-central1 --allow-unauthenticated'
        process = subprocess.run(deploy_command, shell=True, check=True, text=True, capture_output=True)
        logger.info(f"Deployment output: {process.stdout}")

        logger.info("Successfully deployed to Google Cloud Run.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during deployment: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error during deployment: {str(e)}")

if __name__ == "__main__":
    deploy_to_gcloud()
