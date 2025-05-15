#!/bin/bash

# Script to check the DATABASE_URL secret in Google Cloud Secret Manager

echo "===== Checking DATABASE_URL Secret ====="

# Get the secret value (masked for security)
SECRET_VALUE=$(gcloud secrets versions access latest --secret="mobilize-db-url" --project="mobilize-crm")

# Check if the secret value contains 'localhost'
if [[ $SECRET_VALUE == *"localhost"* ]]; then
  echo "ERROR: The DATABASE_URL secret contains 'localhost', which won't work in Cloud Run."
  echo "The secret needs to be updated to point to your Supabase PostgreSQL database."
  
  # Mask the secret value for display (show only the beginning)
  MASKED_VALUE=$(echo $SECRET_VALUE | sed 's/\(postgresql:\/\/[^:]*\):.*/\1:****@****/')
  echo "Current value (masked): $MASKED_VALUE"
  
  echo "\nTo update the secret with the correct Supabase PostgreSQL URL, run:"
  echo "gcloud secrets versions add mobilize-db-url --data-file=/path/to/file/containing/database/url"
  echo "\nThe correct format should be something like:"
  echo "postgresql://postgres.fwnitauuyzxnsvgsbrzr:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
else
  # Mask the secret value for display (show only the beginning)
  MASKED_VALUE=$(echo $SECRET_VALUE | sed 's/\(postgresql:\/\/[^:]*\):.*/\1:****@****/')
  echo "The DATABASE_URL secret appears to be correctly configured."
  echo "Value (masked): $MASKED_VALUE"
fi

echo "\n===== Check Complete ====="
