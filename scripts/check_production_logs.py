#!/usr/bin/env python3
"""
Script to check production logs for errors in the Cloud Run service.
"""

import subprocess
import sys
import os
import re
from datetime import datetime

def check_cloud_run_logs():
    """Check Cloud Run logs for errors and print them in a readable format."""
    print("Checking Cloud Run logs for errors...")
    
    # Get the most recent errors
    cmd = "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm AND severity>=ERROR\" --limit=10 --format=json"
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("No error logs found. Checking for all recent logs...")
            # If no errors, get any recent logs
            cmd = "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm\" --limit=20 --format=json"
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        
        # Parse and print logs in a readable format
        import json
        logs = json.loads(result.stdout) if result.stdout.strip() else []
        
        if not logs:
            print("No logs found. Service might be completely down or logs are not being generated.")
            return False
            
        print(f"Found {len(logs)} log entries:")
        for i, log in enumerate(logs):
            timestamp = log.get('timestamp', 'Unknown time')
            message = log.get('textPayload', log.get('jsonPayload', {}).get('message', 'No message'))
            severity = log.get('severity', 'INFO')
            
            print(f"\n--- Log Entry {i+1} ({severity}) ---")
            print(f"Time: {timestamp}")
            print(f"Message: {message}")
            
            # If there's a stack trace, print it
            if 'jsonPayload' in log and 'stack_trace' in log['jsonPayload']:
                print("\nStack Trace:")
                print(log['jsonPayload']['stack_trace'])
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running gcloud command: {e}")
        print(f"Output: {e.output}")
        return False

def check_service_status():
    """Check the status of the Cloud Run service."""
    print("\nChecking Cloud Run service status...")
    
    cmd = "gcloud run services describe mobilize-crm --region us-central1 --format=\"value(status.conditions)\""
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        status_output = result.stdout.strip()
        
        print(f"Service Status: {status_output}")
        
        # Check if there are any failed revisions
        cmd = "gcloud run revisions list --service mobilize-crm --region us-central1 --format=\"table(revision,status.conditions)\""
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        
        print("\nRecent Revisions Status:")
        print(result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error checking service status: {e}")
        print(f"Output: {e.output}")
        return False

if __name__ == "__main__":
    print(f"=== Production Log Check ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    check_cloud_run_logs()
    check_service_status()
    print("\nLog check complete. Use this information to diagnose the 'Service Unavailable' issue.")