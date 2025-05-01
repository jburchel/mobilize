#!/bin/bash
# Commands to set up GCP secrets for the Mobilize CRM application

# 1. Create the database URL secret
echo "postgresql://postgres:postgres@fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres?sslmode=require" | \
  gcloud secrets create mobilize-db-url \
  --data-file=- \
  --replication-policy="automatic"

# 2. Create the Flask secret key
echo "your-production-secret-key-replace-with-strong-random-value" | \
  gcloud secrets create mobilize-flask-secret \
  --data-file=- \
  --replication-policy="automatic"

# 3. Create the Firebase credentials secret
# Note: This assumes you have a JSON file for Firebase credentials
# gcloud secrets create firebase-credentials \
#   --data-file=/path/to/firebase-credentials.json \
#   --replication-policy="automatic"

# 4. Grant access to the service account
gcloud secrets add-iam-policy-binding mobilize-db-url \
  --member=serviceAccount:mobilize-crm-service-account@mobilize-crm.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

gcloud secrets add-iam-policy-binding mobilize-flask-secret \
  --member=serviceAccount:mobilize-crm-service-account@mobilize-crm.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

gcloud secrets add-iam-policy-binding firebase-credentials \
  --member=serviceAccount:mobilize-crm-service-account@mobilize-crm.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# 5. Verify the secrets have been created
gcloud secrets list 