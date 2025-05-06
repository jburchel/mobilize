#!/usr/bin/env python3
"""
Fix chart rendering in the dashboard template
"""

import re

# Path to the dashboard template file
template_file = "app/templates/dashboard/index.html"

# Read the file content
with open(template_file, 'r') as f:
    content = f.read()

# Fix 1: Update the chart data preparation to handle both 'count' and 'contact_count' fields
count_pattern = r'const counts = data\.stages\.map\(stage => stage\.contact_count\);'
count_replacement = 'const counts = data.stages.map(stage => stage.contact_count || stage.count || 0);'

# Perform the replacement
modified_content = re.sub(count_pattern, count_replacement, content)

# Fix 2: Add console logging to help debug the data structure
logging_code = "\n    // Log the raw data structure\n    console.log('Raw chart data:', data);\n"
replacement_point = "// Prepare chart data"
modified_content = modified_content.replace(replacement_point, replacement_point + logging_code)

# Write the modified content back to the file
with open(template_file, 'w') as f:
    f.write(modified_content)

print("Chart rendering fixed! The template now handles both 'count' and 'contact_count' fields.")
