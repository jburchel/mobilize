#!/usr/bin/env python3
"""
Script to archive unnecessary files that are no longer needed for regular operation.
This helps clean up the codebase without permanently deleting potentially useful scripts.
"""

import os
import shutil
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define root directory
ROOT_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = ROOT_DIR / "scripts" / "archive"

# Files to archive (relative to ROOT_DIR)
FILES_TO_ARCHIVE = [
    # Deployment migration/fix scripts
    "scripts/deployment/fix_connection.py",
    "scripts/deployment/update_db_config.py",
    "scripts/deployment/update_app_config.py",
    "scripts/deployment/verify_data.py",
    "scripts/deployment/verify_migration.py",
    "scripts/deployment/verify_app_config.py",
    "scripts/deployment/extract_sqlite_data.py",
    
    # Cleanup scripts
    "scripts/cleanup_communications_files.py",
    "scripts/cleanup_routes_directory.py",
    "scripts/restore_communications_files.py",
]

# Directories to archive (relative to ROOT_DIR)
DIRS_TO_ARCHIVE = [
    "scripts/deployment/archive",
]

def create_archive_directory():
    """Create the archive directory if it doesn't exist."""
    if not ARCHIVE_DIR.exists():
        ARCHIVE_DIR.mkdir(parents=True)
        logger.info(f"Created archive directory: {ARCHIVE_DIR}")
    return True

def archive_files():
    """Move unnecessary files to the archive directory."""
    for file_path in FILES_TO_ARCHIVE:
        src_path = ROOT_DIR / file_path
        if not src_path.exists():
            logger.warning(f"File not found: {src_path}")
            continue
            
        # Create target directory structure in archive
        rel_path = src_path.relative_to(ROOT_DIR)
        dst_dir = ARCHIVE_DIR / rel_path.parent.relative_to("scripts")
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        # Move the file
        dst_path = dst_dir / src_path.name
        shutil.move(src_path, dst_path)
        logger.info(f"Archived: {src_path} -> {dst_path}")

def archive_directories():
    """Move unnecessary directories to the archive directory."""
    for dir_path in DIRS_TO_ARCHIVE:
        src_path = ROOT_DIR / dir_path
        if not src_path.exists():
            logger.warning(f"Directory not found: {src_path}")
            continue
            
        # Create target directory structure in archive
        rel_path = src_path.relative_to(ROOT_DIR / "scripts")
        dst_path = ARCHIVE_DIR / rel_path
        
        # Create parent directory if needed
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move the directory
        if dst_path.exists():
            # If destination exists, merge contents
            for item in src_path.glob('*'):
                target = dst_path / item.name
                if item.is_dir():
                    shutil.copytree(item, target, dirs_exist_ok=True)
                    shutil.rmtree(item)
                else:
                    shutil.move(item, target)
            logger.info(f"Merged directory: {src_path} -> {dst_path}")
            # Remove the now-empty source directory
            if not any(src_path.iterdir()):
                src_path.rmdir()
        else:
            # If destination doesn't exist, move the whole directory
            shutil.move(src_path, dst_path)
            logger.info(f"Archived directory: {src_path} -> {dst_path}")

def main():
    """Main function to archive unnecessary files."""
    try:
        logger.info("Starting archival of unnecessary files...")
        
        # Create archive directory
        if not create_archive_directory():
            return False
            
        # Archive files and directories
        archive_files()
        archive_directories()
        
        logger.info("Successfully archived unnecessary files.")
        return True
    except Exception as e:
        logger.error(f"Error during archival process: {str(e)}")
        return False

if __name__ == "__main__":
    main()