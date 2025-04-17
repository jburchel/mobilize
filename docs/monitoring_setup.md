# Monitoring Setup Guide for Mobilize CRM

This document provides instructions for setting up comprehensive monitoring for the Mobilize CRM application in a production environment.

## Overview

A robust monitoring solution for Mobilize CRM consists of:

1. Application Performance Monitoring
2. Infrastructure Monitoring
3. Log Management
4. Alerting
5. Dashboard Visualization

## Google Cloud Monitoring Setup

### Prerequisites

- Mobilize CRM deployed on Google Cloud Platform
- IAM permissions to set up monitoring resources
- Google Cloud Operations suite enabled (Monitoring and Logging)

### 1. Set Up Cloud Monitoring

#### Enable Required APIs

```bash
gcloud services enable monitoring.googleapis.com
gcloud services enable cloudtrace.googleapis.com
gcloud services enable clouddebugger.googleapis.com
gcloud services enable cloudprofiler.googleapis.com
```

#### Create Custom Dashboards

1. Navigate to the Google Cloud Console
2. Go to "Monitoring" > "Dashboards"
3. Click "Create Dashboard"
4. Add the following widgets:
   - CPU and Memory usage for Cloud Run services
   - Request count and latency metrics
   - Error rate
   - Database query performance

### 2. Configure Application Metrics

#### Add OpenTelemetry to Your Application

Update `requirements.txt` to include:

```
opentelemetry-api>=1.11.1
opentelemetry-sdk>=1.11.1
opentelemetry-exporter-gcp-trace>=1.0.0
opentelemetry-instrumentation-flask>=0.30b1
```

#### Instrument Your Flask Application

Create a file named `monitoring.py` in your application:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

def configure_monitoring(app):
    """Configure OpenTelemetry for the Flask application."""
    tracer_provider = TracerProvider()
    cloud_trace_exporter = CloudTraceSpanExporter()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(cloud_trace_exporter)
    )
    trace.set_tracer_provider(tracer_provider)
    
    # Instrument Flask
    FlaskInstrumentor().instrument_app(app)
    
    return app
```

Then in your `app.py`:

```python
from monitoring import configure_monitoring

# After creating your Flask app
app = Flask(__name__)
# ... other configuration
app = configure_monitoring(app)
```

### 3. Set Up Custom Metrics

Create custom metrics to track business-specific events:

```python
from google.cloud import monitoring_v3

def create_custom_metric(metric_type, value, resource_labels=None):
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"
    
    series = monitoring_v3.TimeSeries()
    series.metric.type = f"custom.googleapis.com/{metric_type}"
    
    # Add resource labels if provided
    if resource_labels:
        for key, value in resource_labels.items():
            series.resource.labels[key] = value
    
    point = series.points.add()
    point.value.double_value = value
    now = time.time()
    point.interval.end_time.seconds = int(now)
    
    client.create_time_series(name=project_name, time_series=[series])
```

Example usage:

```python
# Track successful user logins
@app.route('/login', methods=['POST'])
def login():
    # ... login logic
    if login_successful:
        create_custom_metric('user_logins', 1)
```

### 4. Configure Uptime Checks

1. Go to "Monitoring" > "Uptime Checks"
2. Click "Create Uptime Check"
3. Configure the check:
   - Title: "Mobilize CRM API Health"
   - Target: HTTPS
   - Resource Type: URL
   - Hostname: your-app-url.run.app
   - Path: /api/health
   - Check frequency: 1 minute

### 5. Set Up Log-based Metrics

1. Go to "Logging" > "Logs Explorer"
2. Create a query to find error logs:
   ```
   resource.type="cloud_run_revision"
   resource.labels.service_name="mobilize-crm"
   severity>=ERROR
   ```
3. Click "Create Metric"
4. Configure the metric:
   - Name: error_count
   - Type: Counter
   - Field name: severity
   - Label: error_type

## Alerting Configuration

### 1. Create Alert Policies

1. Go to "Monitoring" > "Alerting"
2. Click "Create Policy"
3. Configure the following alert policies:

#### High Error Rate Alert

- Metric: logging/user/error_count
- Condition: Any time series violates
- Threshold: > 5 errors in 5 minutes
- Notification channels: Email and/or Slack

#### Service Latency Alert

- Metric: run.googleapis.com/request_latencies
- Condition: Any time series violates
- Threshold: 95th percentile > 500ms over 5 minutes
- Notification channels: Email and/or Slack

#### Database Connection Failures

- Metric: Custom metric for database connection failures
- Condition: Any time series violates
- Threshold: > 3 failures in 5 minutes
- Notification channels: Email and/or Slack

### 2. Configure Notification Channels

1. Go to "Monitoring" > "Alerting" > "Edit Notification Channels"
2. Set up the following channels:
   - Email notifications for critical issues
   - Slack webhook for team notifications
   - PagerDuty for on-call rotation (optional)

## Log Management

### 1. Set Up Log Exports

Export logs to BigQuery for long-term storage and analysis:

```bash
gcloud logging sinks create mobilize-crm-logs \
    bigquery.googleapis.com/projects/YOUR_PROJECT_ID/datasets/mobilize_logs \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="mobilize-crm"'
```

### 2. Create a Log View

1. Go to "Logging" > "Logs Explorer"
2. Create a query for your application logs
3. Click "Save View"
4. Name it "Mobilize CRM Production Logs"

## Dashboard Creation

### 1. Create a Custom Operations Dashboard

Create a comprehensive dashboard that includes:

1. Application Status
   - Uptime percentage
   - Request count and error rate
   - Response latency (P50, P95, P99)
   
2. Resource Utilization
   - CPU usage
   - Memory usage
   - Network traffic
   
3. Database Metrics
   - Query performance
   - Connection pool status
   - Database errors
   
4. Business Metrics
   - Active users
   - Key user actions (logins, form submissions, etc.)
   - Critical business process completion rates

## Integrating with Third-Party Monitoring Tools

### Datadog Integration (Optional)

If using Datadog for monitoring:

1. Install the Datadog agent on your GCP project
2. Configure Google Cloud integration in Datadog
3. Set up Datadog APM for Python applications

### New Relic Integration (Optional)

If using New Relic for monitoring:

1. Add New Relic Python agent to `requirements.txt`:
   ```
   newrelic>=7.2.0.167
   ```
   
2. Create a New Relic configuration file (`newrelic.ini`)

3. Update your application startup script to include New Relic:
   ```bash
   NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program gunicorn app:app
   ```

## Troubleshooting Monitoring Issues

### Missing Metrics

If metrics are not appearing:

1. Verify the application is properly instrumented
2. Check IAM permissions for the service account
3. Ensure the appropriate APIs are enabled
4. Verify the correct project ID is being used

### False Alerts

If receiving false positive alerts:

1. Adjust alert thresholds based on observed baseline performance
2. Add additional conditions to alert policies
3. Implement alert grouping to reduce noise

## Best Practices

1. Monitor both technical and business metrics
2. Set up alerts for anomalies, not just threshold violations
3. Create separate dashboards for different user roles (developers, operations, business)
4. Regularly review and update monitoring configuration as the application evolves
5. Document alert response procedures
6. Implement automated remediation for common issues when possible
7. Configure proper log rotation and retention policies
8. Use structured logging to make logs more searchable and analyzable 