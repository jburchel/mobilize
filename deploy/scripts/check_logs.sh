#!/bin/bash

set -e

# Mobilize CRM Log Checker
# This script helps check logs from the Cloud Run service

echo "===== Checking Mobilize CRM Logs ====="

# Parse command line arguments
SEVERITY="INFO"
LIMIT=20
FRESHNESS="1h"

while [[ $# -gt 0 ]]; do
  case $1 in
    --severity)
      SEVERITY="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --freshness)
      FRESHNESS="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--severity LEVEL] [--limit NUM] [--freshness TIME]"
      echo "  --severity LEVEL   Log severity: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)"
      echo "  --limit NUM        Number of log entries to display (default: 20)"
      echo "  --freshness TIME   How fresh the logs should be: 1h, 1d, etc. (default: 1h)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Build the filter based on severity
if [ "$SEVERITY" = "DEBUG" ]; then
  FILTER="resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm"
else
  FILTER="resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm AND severity>=${SEVERITY}"
fi

echo "Fetching logs with severity >= $SEVERITY, limit $LIMIT, freshness $FRESHNESS"
echo "Filter: $FILTER"
echo ""

# Fetch the logs
gcloud logging read "$FILTER" --limit $LIMIT --freshness=$FRESHNESS --format="table(timestamp,severity,textPayload)"

echo ""
echo "===== Log Check Complete ====="
echo "For more detailed logs, visit the Google Cloud Console:"
echo "https://console.cloud.google.com/logs/query?project=mobilize-crm"
