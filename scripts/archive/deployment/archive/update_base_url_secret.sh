#!/bin/bash

set -e

echo "Updating BASE_URL secret in Secret Manager..."

# Create a temporary file with the new BASE_URL value
echo -n "https://mobilize-crm.org" > /tmp/base_url.txt

# Update the secret in Secret Manager
gcloud secrets versions add mobilize-base-url --data-file=/tmp/base_url.txt

echo "BASE_URL secret updated successfully!"
echo "Restarting the Cloud Run service to apply the changes..."

# Restart the Cloud Run service by updating it with no changes
gcloud run services update mobilize-crm --region us-central1 --no-traffic
gcloud run services update mobilize-crm --region us-central1 --traffic=100

echo "Cloud Run service restarted successfully!"
