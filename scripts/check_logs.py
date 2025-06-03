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

        # Run gcloud command to fetch logs - specifically looking for Communications and Email errors
        logs_command = 'gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm AND (textPayload:communications OR textPayload:emails OR textPayload:email_signature OR textPayload:EmailSignature)" --limit 50 --format "value(textPayload)"'
        process = subprocess.run(logs_command, shell=True, check=True, text=True, capture_output=True)
        logs = process.stdout.strip()
        logger.info(f"Recent logs related to Communications and Email Management:\n{logs}")
        
        # Also check for error logs
        error_logs_command = 'gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm AND severity>=ERROR" --limit 20 --format "value(textPayload)"'
        error_process = subprocess.run(error_logs_command, shell=True, check=True, text=True, capture_output=True)
        error_logs = error_process.stdout.strip()
        logger.info(f"Recent error logs:\n{error_logs}")

        # Check for errors in logs
        if 'error' in logs.lower() or 'exception' in logs.lower() or 'traceback' in logs.lower():
            logger.warning("Potential errors found in Communications/Email logs. Please review for specific issues.")
        elif error_logs:
            logger.warning("Errors found in general application logs. Please review for specific issues.")
        else:
            logger.info("No obvious errors found in recent logs.")

        logger.info("Successfully checked logs.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking logs: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error checking logs: {str(e)}")

if __name__ == "__main__":
    check_logs()
