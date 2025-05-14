#!/bin/bash

set -e

echo "Updating environment variables for Cloud Run service..."
gcloud run services update mobilize-crm \
    --region us-central1 \
    --update-env-vars BASE_URL=https://mobilize-crm.org

echo "Environment variables updated successfully!"
