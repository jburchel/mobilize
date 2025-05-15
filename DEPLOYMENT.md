# Mobilize CRM Deployment Process

## Overview

This document outlines the deployment process for the Mobilize CRM application to Google Cloud Run.

## Deployment Method

We use a manual deployment process with the `fix_deploy.sh` script located in the `deploy/scripts` directory. The automatic Cloud Build trigger should be disabled.

## Deployment Steps

1. Make your code changes and test them locally
2. Commit your changes to the repository
3. Push your changes to the main branch
4. Run the deployment script:

   ```bash
   ./deploy/scripts/fix_deploy.sh
   ```

5. Wait for the deployment to complete (this may take a few minutes)
6. Verify the deployment by checking the application at [https://mobilize-crm.org](https://mobilize-crm.org)

## Checking Logs

To check the logs for any issues:

```bash
./deploy/scripts/check_logs.sh --severity ERROR --freshness 5m
```

For more detailed logs:

```bash
./deploy/scripts/check_logs.sh --severity INFO --limit 20
```

## Deployment Configuration

The deployment configuration is set up to use the following environment variables and secrets:

- `DATABASE_URL`: Secret containing the Supabase PostgreSQL connection string
- `FIREBASE_CREDENTIALS`: Secret containing the Firebase credentials
- `SECRET_KEY`: Secret containing the Flask secret key
- `GOOGLE_CLIENT_ID`: Secret containing the Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Secret containing the Google OAuth client secret


Environment variables:

- `FLASK_APP`: Set to `app.py`
- `FLASK_ENV`: Set to `production`
- `LOG_LEVEL`: Set to `INFO`
- `LOG_TO_STDOUT`: Set to `True`
- `PREFERRED_URL_SCHEME`: Set to `https`
