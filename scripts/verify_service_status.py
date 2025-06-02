import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_service_status():
    try:
        logger.info("Verifying service status for Mobilize-CRM...")
        service_url = "https://mobilize-crm-x3exfzl3zq-uc.a.run.app"
        response = requests.get(service_url, timeout=30)
        if response.status_code == 200:
            logger.info("Service is up and running. 'Service Unavailable' error resolved.")
            if 'Service Unavailable' in response.text:
                logger.warning("Service is responding but 'Service Unavailable' message found in content.")
            else:
                logger.info("No 'Service Unavailable' message found in content.")
        else:
            logger.warning(f"Service returned status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error verifying service status: {str(e)}")

if __name__ == "__main__":
    verify_service_status()
