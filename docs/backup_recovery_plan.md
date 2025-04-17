# Backup and Recovery Plan for Mobilize CRM

This document outlines the backup and recovery procedures for the Mobilize CRM application to ensure data protection and business continuity.

## Backup Strategy

### Data Assets to Backup

1. **Database**
   - SQL database containing all customer data, user accounts, and application state
   - GCS bucket data (file attachments, documents, images)

2. **Application Code**
   - Source code repositories
   - Configuration files
   - Environment variables

3. **Infrastructure Configuration**
   - Infrastructure as Code (IaC) files
   - CI/CD pipeline configurations
   - Cloud service configurations

### Backup Schedule and Retention

| Data Type | Backup Frequency | Retention Period | Storage Location |
|-----------|------------------|------------------|------------------|
| Database (full) | Daily | 30 days | GCS backup bucket |
| Database (incremental) | Hourly | 7 days | GCS backup bucket |
| Transaction logs | Every 15 minutes | 3 days | GCS backup bucket |
| GCS bucket data | Daily | 30 days | GCS backup bucket |
| Application code | On every commit | Indefinite | Git repository |
| Infrastructure config | On change | 90 days | Git repository |

## Backup Implementation

### Database Backups

#### CloudSQL Automated Backups

```bash
# Enable automated backups for CloudSQL instance
gcloud sql instances patch mobilize-db \
  --backup-start-time="00:00" \
  --backup-location="us-central1" \
  --retained-backups-count=30

# Verify backup configuration
gcloud sql instances describe mobilize-db \
  --format="default(settings.backupConfiguration)"
```

#### Export Database to GCS

```bash
# Create daily export job
gcloud scheduler jobs create http mobilize-db-export-daily \
  --schedule="0 2 * * *" \
  --uri="https://sqladmin.googleapis.com/v1/projects/PROJECT_ID/instances/mobilize-db/export" \
  --http-method=POST \
  --oauth-service-account-email=backup-service-account@PROJECT_ID.iam.gserviceaccount.com \
  --headers="Content-Type: application/json" \
  --message-body='{
    "exportContext": {
      "fileType": "SQL",
      "uri": "gs://mobilize-backups/database/daily/mobilize-db-$(date +%Y-%m-%d).sql",
      "databases": ["mobilize_production"],
      "offload": true
    }
  }'
```

### GCS Storage Backups

```bash
# Create daily GCS bucket sync job
gcloud scheduler jobs create http mobilize-gcs-backup-daily \
  --schedule="0 3 * * *" \
  --uri="https://cloudfunctions.googleapis.com/v1/projects/PROJECT_ID/locations/us-central1/functions/syncBuckets:trigger" \
  --http-method=POST \
  --oauth-service-account-email=backup-service-account@PROJECT_ID.iam.gserviceaccount.com \
  --headers="Content-Type: application/json" \
  --message-body='{
    "source": "mobilize-storage",
    "destination": "mobilize-backups/storage/daily/$(date +%Y-%m-%d)"
  }'
```

### Application Code Backup

Ensure repository mirroring is set up for your Git repositories:

```bash
# Set up repository mirroring (GitHub example)
git remote add backup https://github.com/backup-org/mobilize-crm-backup.git
git push --mirror backup
```

Configure automated mirror updates via CI/CD pipeline.

## Disaster Recovery Procedures

### Recovery Time Objectives (RTO)

| Component | Recovery Time Objective |
|-----------|--------------------------|
| Database | 1 hour |
| Storage | 4 hours |
| Application | 2 hours |
| Complete system | 8 hours |

### Database Recovery

#### From CloudSQL Automated Backup

```bash
# List available backups
gcloud sql backups list --instance=mobilize-db

# Restore database from backup
gcloud sql instances restore mobilize-db \
  --restore-backup-name=BACKUP_ID
```

#### From GCS Export

```bash
# Import database from GCS
gcloud sql import sql mobilize-db \
  gs://mobilize-backups/database/daily/mobilize-db-YYYY-MM-DD.sql \
  --database=mobilize_production
```

### Storage Recovery

```bash
# Restore GCS bucket contents
gcloud storage cp -r gs://mobilize-backups/storage/daily/YYYY-MM-DD/* gs://mobilize-storage/
```

### Application Deployment Recovery

```bash
# Deploy specific version
gcloud run deploy mobilize-crm \
  --image=gcr.io/PROJECT_ID/mobilize-crm:VERSION \
  --region=us-central1
```

## Testing and Verification

### Backup Testing Schedule

| Test Type | Frequency | Responsible Team |
|-----------|-----------|------------------|
| Database restore test | Monthly | Database Admin |
| Storage restore test | Quarterly | DevOps |
| Full disaster recovery test | Bi-annually | All Teams |

### Backup Verification Process

1. **Automated Verification**
   - Run integrity checks on all database backups
   - Verify backup completion and file size

   ```bash
   # Automated backup verification function
   function verify_backup() {
     BACKUP_PATH=$1
     # Check if backup exists
     gsutil stat $BACKUP_PATH >/dev/null 2>&1
     if [ $? -ne 0 ]; then
       echo "Backup not found: $BACKUP_PATH"
       exit 1
     fi
     
     # Check backup size
     SIZE=$(gsutil du -s $BACKUP_PATH | awk '{print $1}')
     if [ $SIZE -lt 1000000 ]; then  # Less than 1MB
       echo "Backup too small: $BACKUP_PATH ($SIZE bytes)"
       exit 1
     fi
     
     echo "Backup verified: $BACKUP_PATH ($SIZE bytes)"
     exit 0
   }
   ```

2. **Manual Verification**
   - Restore backup to test environment
   - Run application tests against restored data
   - Verify data consistency and integrity

## Recovery Documentation

### Emergency Contacts

| Role | Name | Contact Information | Responsibilities |
|------|------|---------------------|------------------|
| Primary Database Admin | [Name] | [Phone/Email] | Database recovery |
| Backup Database Admin | [Name] | [Phone/Email] | Database recovery backup |
| DevOps Lead | [Name] | [Phone/Email] | Infrastructure recovery |
| Application Lead | [Name] | [Phone/Email] | Application deployment |
| Security Officer | [Name] | [Phone/Email] | Security assessment |

### Recovery Scenarios

#### Scenario 1: Database Corruption

1. Identify extent of corruption
2. Stop application services to prevent further damage
3. Restore latest valid database backup
4. Apply transaction logs if available
5. Verify data integrity
6. Restart application services

#### Scenario 2: Cloud Service Region Outage

1. Activate failover plan
2. Switch DNS to backup region
3. Promote database replica to primary
4. Verify application functionality
5. Monitor performance and stability

#### Scenario 3: Ransomware/Security Breach

1. Isolate affected systems
2. Assess damage and breach scope
3. Restore systems from known clean backups
4. Apply security patches and updates
5. Perform security audit before resuming operations
6. Document incident and report to relevant authorities

## Continuous Improvement

### Backup Metrics to Monitor

- Backup completion time
- Backup size and growth rate
- Restore test success rate
- Recovery time during tests

### Plan Review Schedule

- Review backup and recovery plan quarterly
- Update after major system changes
- Incorporate lessons learned from tests and actual recovery events

## Appendix: Recovery Runbooks

### A1: Full System Recovery Runbook

```
# Full System Recovery Procedure

## Step 1: Assessment
- Identify affected components
- Document current state
- Assemble recovery team

## Step 2: Infrastructure Recovery
- Provision new infrastructure if needed
- Restore infrastructure configuration
- Verify networking and security

## Step 3: Database Recovery
- Restore database from latest backup
- Apply transaction logs
- Verify data integrity
- Run consistency checks

## Step 4: Storage Recovery
- Restore GCS bucket contents
- Verify file integrity
- Check permissions

## Step 5: Application Deployment
- Deploy latest stable application version
- Configure environment variables
- Verify service connectivity

## Step 6: Testing and Verification
- Run smoke tests
- Verify critical functionality
- Perform security checks

## Step 7: Go-Live
- Update DNS/routing
- Monitor system performance
- Document recovery process
```

### A2: Data Corruption Investigation Process

Document steps to identify the root cause of data corruption to prevent future occurrences:

1. Analyze database logs
2. Review application logs
3. Check for unusual access patterns
4. Review recent code changes
5. Document findings and implement preventive measures 