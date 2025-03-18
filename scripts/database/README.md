# Database Scripts

This directory contains scripts for database operations, including migrations, seeding, and maintenance.

## Available Scripts

### migrate_to_supabase.py
- Purpose: Creates and initializes the database schema in Supabase
- Usage: `python scripts/database/migrate_to_supabase.py`
- Requirements: 
  - `.env.production` file with valid Supabase connection string
  - `psycopg2-binary` package installed

## Adding New Scripts

When adding new database scripts:
1. Follow the naming convention: `purpose_action.py`
2. Include proper error handling and logging
3. Add documentation in this README
4. Test thoroughly in development environment first 