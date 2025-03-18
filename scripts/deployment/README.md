# Deployment Scripts

This directory contains scripts for deploying the Mobilize CRM application to various environments.

## Script Categories

### Environment Setup
Scripts for setting up development, staging, and production environments.

### Deployment Automation
Scripts for automating the deployment process to Google Cloud Run and other services.

### Configuration Management
Scripts for managing environment variables and configuration files.

## Adding New Scripts

When adding new deployment scripts:
1. Follow the naming convention: `environment_action.sh` or `environment_action.py`
2. Include proper error handling and rollback procedures
3. Add documentation in this README
4. Test in a staging environment before using in production 