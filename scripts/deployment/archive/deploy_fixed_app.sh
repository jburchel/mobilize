#!/bin/bash

set -e

echo "Building fixed Docker image..."
gcloud builds submit --tag gcr.io/mobilize-crm/mobilize-crm:fixed

echo "Deploying fixed application to Cloud Run..."
gcloud run deploy mobilize-crm \
    --image gcr.io/mobilize-crm/mobilize-crm:fixed \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --update-env-vars FLASK_APP=app,FLASK_ENV=production,PREFERRED_URL_SCHEME=https,BASE_URL=https://mobilize-crm.org \
    --update-secrets=DB_CONNECTION_STRING=DB_CONNECTION_STRING:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest

echo "Deployment complete!"
