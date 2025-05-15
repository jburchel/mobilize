#!/bin/bash

# Script to update environment variables for the Mobilize CRM Cloud Run service

echo "===== Updating Environment Variables for Mobilize CRM ====="

# Update the Cloud Run service to add the BASE_URL environment variable
gcloud run services update mobilize-crm \
  --region=us-central1 \
  --update-env-vars="BASE_URL=https://mobilize-crm.org"

echo "===== Environment Variables Updated ====="
echo "The BASE_URL environment variable has been added to the Cloud Run service."
echo "Next, you need to update the Google OAuth client configuration in the Google Cloud Console."
echo "Follow the instructions in the GOOGLE_OAUTH_FIX.md file to complete the fix."
