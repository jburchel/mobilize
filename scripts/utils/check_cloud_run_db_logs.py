#!/usr/bin/env python3
"""
Cloud Run Database Connection Log Checker

This script queries Google Cloud Logs to extract database connection information
from the Cloud Run service logs. It helps identify database connection issues
in your deployed application.

Requirements:
- Authenticated gcloud CLI
- google-cloud-logging Python package

Usage:
python3 check_cloud_run_db_logs.py [--project PROJECT_ID] [--service SERVICE_NAME] [--hours HOURS]
"""

import argparse
import datetime
import sys
import re
from google.cloud import logging
from google.cloud.logging_v2.types import ListLogEntriesRequest

# Database connection patterns to look for
DB_PATTERNS = [
    r"(postgresql://[^:]+:[^@]+@[^/]+/[^?]+(\?[^'\"]+)?)",  # Database URLs
    r"(database connection|db connection|connecting to.*database)",  # Connection attempts
    r"(database error|db error|connection failed|could not connect)",  # Connection errors
    r"(sqlalchemy\.engine\.Engine|sqlalchemy\.pool\.impl\.QueuePool)",  # SQLAlchemy logs
]

def get_log_entries(project_id, service_name, hours=1):
    """Query Cloud Run logs for database-related entries"""
    client = logging.Client(project=project_id)
    
    # Calculate time range
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(hours=hours)
    
    # Convert times to RFC3339 format
    start_time_str = start_time.isoformat("T") + "Z"
    end_time_str = end_time.isoformat("T") + "Z"
    
    # Create filter for database-related logs
    filter_str = (
        f'resource.type="cloud_run_revision" '
        f'resource.labels.service_name="{service_name}" '
        f'timestamp>="{start_time_str}" '
        f'timestamp<="{end_time_str}" '
        f'('
    )
    
    # Add patterns to the filter
    pattern_filters = []
    for pattern in DB_PATTERNS:
        pattern_filters.append(f'textPayload=~"{pattern}"')
    
    filter_str += " OR ".join(pattern_filters) + ")"
    
    print(f"Querying logs with filter: {filter_str}")
    
    # Create request
    request = ListLogEntriesRequest(
        resource_names=[f"projects/{project_id}"],
        filter=filter_str,
        order_by="timestamp desc"
    )
    
    # Get entries
    entries = client.logging_api.list_log_entries(request=request)
    return entries

def analyze_logs(entries):
    """Analyze log entries for database connection information"""
    connection_attempts = 0
    connection_errors = 0
    successful_connections = 0
    
    # Lists to store results
    errors = []
    connections = []
    
    # Process each entry
    for entry in entries:
        log_text = entry.text_payload if entry.text_payload else str(entry)
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Look for connection attempts
        if re.search(DB_PATTERNS[1], log_text, re.IGNORECASE):
            connection_attempts += 1
        
        # Look for connection errors
        if re.search(DB_PATTERNS[2], log_text, re.IGNORECASE):
            connection_errors += 1
            errors.append(f"{timestamp}: {log_text.strip()}")
        
        # Look for successful connections
        if "connected to postgresql" in log_text.lower() or "connection established" in log_text.lower():
            successful_connections += 1
            connections.append(f"{timestamp}: {log_text.strip()}")
        
        # Extract database URLs
        url_matches = re.search(DB_PATTERNS[0], log_text)
        if url_matches:
            # Redact password from URL for security
            db_url = url_matches.group(1)
            redacted_url = re.sub(r":([^@]+)@", ":****@", db_url)
            print(f"Found database URL: {redacted_url}")
    
    # Print summary
    print("\n=== Database Connection Summary ===")
    print(f"Analyzed logs from: {timestamp}")
    print(f"Connection attempts: {connection_attempts}")
    print(f"Connection errors: {connection_errors}")
    print(f"Successful connections: {successful_connections}")
    
    # Print connection errors
    if errors:
        print("\n=== Connection Errors ===")
        for err in errors[:5]:  # Show first 5 errors
            print(err)
        if len(errors) > 5:
            print(f"... and {len(errors) - 5} more errors (run with --verbose to see all)")
    
    # Print successful connections
    if connections:
        print("\n=== Successful Connections ===")
        for conn in connections[:3]:  # Show first 3 successful connections
            print(conn)
        if len(connections) > 3:
            print(f"... and {len(connections) - 3} more connections")
    
    return connection_attempts, connection_errors, successful_connections

def main():
    """Main function to parse args and check logs"""
    parser = argparse.ArgumentParser(description="Check Cloud Run logs for database connection information")
    parser.add_argument("--project", required=False, help="Google Cloud project ID")
    parser.add_argument("--service", default="mobilize-crm", help="Cloud Run service name")
    parser.add_argument("--hours", type=int, default=1, help="Number of hours to check logs")
    parser.add_argument("--verbose", action="store_true", help="Show all log entries")
    
    args = parser.parse_args()
    
    # Get project ID from gcloud if not provided
    if not args.project:
        try:
            import subprocess
            project = subprocess.check_output(
                ["gcloud", "config", "get-value", "project"], 
                universal_newlines=True
            ).strip()
            if project:
                args.project = project
            else:
                print("Error: Could not determine project ID. Please specify with --project")
                sys.exit(1)
        except Exception as e:
            print(f"Error getting project ID: {e}")
            print("Please specify project ID with --project")
            sys.exit(1)
    
    print(f"Checking database connection logs for {args.service} in {args.project} (last {args.hours} hours)")
    
    try:
        entries = get_log_entries(args.project, args.service, args.hours)
        attempts, errors, successes = analyze_logs(entries)
        
        # Provide recommendation based on analysis
        if errors > 0 and successes == 0:
            print("\nRECOMMENDATION: Database connection is failing. Check connection string and network settings.")
        elif errors > successes * 2:
            print("\nRECOMMENDATION: Intermittent database connection issues detected. Review connection pooling and retry logic.")
        elif successes > 0 and errors == 0:
            print("\nRECOMMENDATION: Database connection appears to be working correctly.")
        else:
            print("\nRECOMMENDATION: Some database connection issues detected. Monitor application performance.")
        
    except Exception as e:
        print(f"Error checking logs: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 