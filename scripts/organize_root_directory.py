#!/usr/bin/env python3
"""
Script to organize the root directory by moving files to appropriate subdirectories.
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

# Files to organize (relative to ROOT_DIR)
ORGANIZATION_PLAN = {
    # Documentation files to docs/
    "docs/": [
        "backup_recovery_plan.md",
        "setup-instructions.md",
        # Add other documentation files here
    ],
    
    # Configuration files to config/
    "config/": [
        "postcss.config.js",
        ".gcloudignore",
        # Don't move critical configs like .env, .gitignore
    ],
    
    # Build scripts to build/
    "build/": [
        "optimize-images.js",
        # Add other build scripts here
    ],
    
    # Keep these files in root (don't move)
    "KEEP_IN_ROOT": [
        ".env",
        ".env.development",
        ".env.production",
        ".gitignore",
        "README.md",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "wsgi.py",
        "start.sh",
        "main.py",
        # Add other critical files here
    ]
}

def create_directories():
    """Create the organization directories if they don't exist."""
    for directory in ORGANIZATION_PLAN.keys():
        if directory != "KEEP_IN_ROOT":
            dir_path = ROOT_DIR / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
    return True

def organize_files():
    """Move files to their appropriate directories."""
    for target_dir, files in ORGANIZATION_PLAN.items():
        if target_dir == "KEEP_IN_ROOT":
            continue
            
        for file_name in files:
            src_path = ROOT_DIR / file_name
            if not src_path.exists():
                logger.warning(f"File not found: {src_path}")
                continue
                
            # Create target directory if needed
            dst_dir = ROOT_DIR / target_dir
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            dst_path = dst_dir / src_path.name
            shutil.move(src_path, dst_path)
            logger.info(f"Moved: {src_path} -> {dst_path}")

def main():
    """Main function to organize root directory."""
    try:
        logger.info("Starting root directory organization...")
        
        # Create organization directories
        create_directories()
        
        # Organize files
        organize_files()
        
        logger.info("Successfully organized root directory.")
        return True
    except Exception as e:
        logger.error(f"Error during organization process: {str(e)}")
        return False

if __name__ == "__main__":
    main()