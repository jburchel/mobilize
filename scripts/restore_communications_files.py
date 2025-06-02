import os
import sys
import shutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define paths
routes_dir = '/Users/jimburchel/Developer-Playground/mobilize-app/app/routes'
backup_dir = os.path.join(routes_dir, 'backup')

# Files to be restored from backup
files_to_restore = [
    'communications_simple.py',
    'communications_simple.py.bak'
]

def restore_files():
    try:
        # Check if backup directory exists
        if not os.path.exists(backup_dir):
            logger.error(f"Backup directory does not exist: {backup_dir}")
            return

        # Move files back from backup to routes directory
        for file_name in files_to_restore:
            src_path = os.path.join(backup_dir, file_name)
            dst_path = os.path.join(routes_dir, file_name)
            if os.path.exists(src_path):
                shutil.move(src_path, dst_path)
                logger.info(f"Restored {file_name} to routes directory")
            else:
                logger.warning(f"File {file_name} not found in backup directory")

        logger.info("Successfully completed restoration of necessary communications files.")
    except Exception as e:
        logger.error(f"Error during restoration: {str(e)}")

if __name__ == "__main__":
    restore_files()
