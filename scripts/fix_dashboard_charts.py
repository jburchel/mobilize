#!/usr/bin/env python3
"""
Fix dashboard charts by updating the pipeline_id in the response data
"""

import re

# Path to the dashboard.py file
dashboard_file = "app/routes/dashboard.py"

# Read the file content
with open(dashboard_file, 'r') as f:
    content = f.read()

# Replace all instances of hardcoded pipeline_id with the actual pipeline_id
pattern = r'"pipeline_id":\s*1,\s*#\s*Use dummy ID'
replacement = '"pipeline_id": pipeline_id,  # Use actual pipeline ID'

# Perform the replacement
modified_content = re.sub(pattern, replacement, content)

# Write the modified content back to the file
with open(dashboard_file, 'w') as f:
    f.write(modified_content)

print("Dashboard charts fixed! The pipeline_id is now correctly set to the actual pipeline ID.")
