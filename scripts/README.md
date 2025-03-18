# Scripts Directory Structure

This directory contains various scripts used for development, deployment, maintenance, and testing of the Mobilize CRM application.

## Directory Structure

### /database
Scripts related to database operations, including:
- Database migrations
- Data seeding
- Backup and restore
- Schema management
- Data cleanup and maintenance

### /deployment
Scripts for deploying the application, including:
- Deployment automation
- Environment setup
- Configuration management
- Service initialization
- SSL/TLS certificate management

### /maintenance
Scripts for system maintenance, including:
- Log rotation
- Cache clearing
- System health checks
- Automated backups
- Performance monitoring

### /testing
Scripts for testing purposes, including:
- Test data generation
- Load testing
- Integration test setup
- API testing
- Performance benchmarking

### /utils
Utility scripts for development and operations, including:
- Environment setup
- Development tools
- Code generation
- Documentation generation
- Helper functions and tools

## Usage

Each script should:
1. Include a docstring or header comment explaining its purpose
2. List any required environment variables or configuration
3. Include error handling and logging
4. Be executable from the project root directory
5. Follow the naming convention: `purpose_action.py` (e.g., `db_migrate.py`, `deploy_production.sh`)

## Examples

```bash
# Running a database migration
python scripts/database/migrate_to_supabase.py

# Running deployment script
./scripts/deployment/deploy_to_production.sh

# Running maintenance tasks
python scripts/maintenance/cleanup_logs.py

# Running tests
python scripts/testing/load_test.py
```

## Adding New Scripts

When adding new scripts:
1. Place them in the appropriate subdirectory
2. Update this README if adding a new category
3. Ensure they follow the project's coding standards
4. Include appropriate documentation
5. Test thoroughly before committing 