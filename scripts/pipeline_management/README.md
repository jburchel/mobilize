# Pipeline Management Scripts

This directory contains scripts for managing the pipeline feature in the Mobilize CRM application.

## Available Scripts

### create_pipeline_tables.py
Creates the necessary database tables for the pipeline feature.

### populate_pipelines.py
Populates the pipeline tables with initial data.

### check_pipelines.py
Validates pipeline data and checks for consistency issues.

### fix_pipeline_contacts.py
Repairs issues with pipeline contacts data.

## Usage

Run these scripts from the project root directory with:

```bash
python scripts/pipeline_management/script_name.py
```

Note: These scripts may require the application context to be set up, so run them from the project root directory. 