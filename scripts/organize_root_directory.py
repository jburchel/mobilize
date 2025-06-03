#!/usr/bin/env python3
"""
Script to organize the root directory by moving files to appropriate subdirectories.
"""

import os
import shutil
import logging
import re
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
        # Markdown documentation
        "*.md",
        "*.MD",
        "CONTRIBUTING*",
        "CHANGELOG*",
        "LICENSE*",
        "CODE_OF_CONDUCT*",
        # Exclude README.md which stays in root
    ],
    
    # Configuration files to config/
    "config/": [
        # Config files
        "*.config.js",
        "*.conf",
        "*.cfg",
        "*.ini",
        ".babelrc",
        ".eslintrc*",
        ".prettierrc*",
        ".stylelintrc*",
        ".gcloudignore",
        "tsconfig.json",
        "jest.config.js",
        "webpack.config.js",
        "babel.config.js",
        "postcss.config.js",
        "tailwind.config.js",
        # Exclude critical configs that should stay in root
    ],
    
    # Build scripts to build/
    "build/": [
        # Build scripts
        "optimize-images.js",
        "build-*.js",
        "*.build.js",
        "rollup.config.js",
        "vite.config.js",
    ],
    
    # Development tools to tools/
    "tools/": [
        # Development utilities
        "*.sh",
        "*.bash",
        "*.bat",
        "*.cmd",
        # Exclude start.sh which stays in root
    ],
    
    # Keep these files in root (don't move)
    "KEEP_IN_ROOT": [
        # Environment files
        ".env",
        ".env.*",
        ".env.development",
        ".env.production",
        ".env.local",
        ".env.test",
        # Git files
        ".git",
        ".gitignore",
        ".gitattributes",
        # Core application files
        "README.md",
        "requirements.txt",
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "Dockerfile",
        "docker-compose.yml",
        "wsgi.py",
        "start.sh",
        "main.py",
        "app.py",
        "manage.py",
        "setup.py",
        "pyproject.toml",
        # Directories to keep in root
        "app/",
        "src/",
        "tests/",
        "scripts/",
        "static/",
        "templates/",
        "migrations/",
        "node_modules/",
        "venv/",
        ".venv/",
        "env/",
        ".env/",
        "dist/",
        "build/",
        "public/",
    ]
}

def should_keep_in_root(file_path):
    """Check if a file should be kept in the root directory."""
    file_name = file_path.name
    rel_path = str(file_path.relative_to(ROOT_DIR))
    
    # Check exact matches
    for pattern in ORGANIZATION_PLAN["KEEP_IN_ROOT"]:
        # If pattern ends with /, it's a directory
        if pattern.endswith('/'):
            if rel_path.startswith(pattern) or rel_path.startswith(pattern[:-1]):
                return True
        # Check for exact match
        elif file_name == pattern:
            return True
        # Check for wildcard match
        elif '*' in pattern and re.match(f"^{pattern.replace('*', '.*')}$", file_name):
            return True
    
    return False

def get_target_directory(file_path):
    """Determine the target directory for a file."""
    file_name = file_path.name
    
    # Skip directories
    if file_path.is_dir():
        return None
        
    # Skip files that should stay in root
    if should_keep_in_root(file_path):
        return None
    
    # Find matching target directory
    for target_dir, patterns in ORGANIZATION_PLAN.items():
        if target_dir == "KEEP_IN_ROOT":
            continue
            
        for pattern in patterns:
            # Check for exact match
            if file_name == pattern:
                return target_dir
            # Check for wildcard match
            elif '*' in pattern and re.match(f"^{pattern.replace('*', '.*')}$", file_name):
                return target_dir
    
    # No match found
    return None

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
    # Get all files in root directory
    root_files = [f for f in ROOT_DIR.glob('*') if f.is_file()]
    
    for file_path in root_files:
        target_dir = get_target_directory(file_path)
        if not target_dir:
            continue
            
        # Create target directory if needed
        dst_dir = ROOT_DIR / target_dir
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        # Move the file
        dst_path = dst_dir / file_path.name
        shutil.move(file_path, dst_path)
        logger.info(f"Moved: {file_path} -> {dst_path}")

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
