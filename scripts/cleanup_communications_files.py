import os
import shutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define paths
routes_dir = '/Users/jimburchel/Developer-Playground/mobilize-app/app/routes'
backup_dir = os.path.join(routes_dir, 'backup')

# Files to be moved to backup
files_to_backup = [
    'communications_fixed.py.bak',
    'communications_robust.py',
    'communications_robust.py.bak',
    'communications_simple.py.bak',
    'communications_test.py',
    'communications_test.py.bak'
]

def cleanup_files():
    try:
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            logger.info(f"Created backup directory: {backup_dir}")

        # Move files to backup
        for file_name in files_to_backup:
            src_path = os.path.join(routes_dir, file_name)
            dst_path = os.path.join(backup_dir, file_name)
            if os.path.exists(src_path):
                shutil.move(src_path, dst_path)
                logger.info(f"Moved {file_name} to backup directory")
            else:
                logger.warning(f"File {file_name} not found in routes directory")

        logger.info("Successfully completed cleanup of communications files.")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    cleanup_files()
