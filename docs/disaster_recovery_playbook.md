# Mobilize CRM Disaster Recovery Playbook

This playbook provides step-by-step procedures for responding to and recovering from disasters affecting the Mobilize CRM application.

## Disaster Classification

| Severity | Description | Examples | Initial Response Time |
|----------|-------------|----------|----------------------|
| Critical | Complete system outage or data loss | Database corruption, ransomware attack | Immediate (< 15 minutes) |
| Major | Significant functionality impacted | Regional outage, major service degradation | < 30 minutes |
| Moderate | Limited functionality impacted | Single component failure, performance issues | < 2 hours |
| Minor | Minimal impact on operations | Non-critical service degradation | < 8 hours |

## Emergency Response Team

### Team Activation

To activate the Disaster Recovery team:

1. Call the emergency hotline: `XXX-XXX-XXXX`
2. Send alert to emergency Slack channel: `#mobilize-emergency`
3. Trigger PagerDuty incident with priority "P1-Critical"

### Team Roles and Responsibilities

| Role | Responsibilities |
|------|-----------------|
| Incident Commander | Overall coordination, communication with stakeholders |
| Technical Lead | Technical assessment, recovery strategy decisions |
| Database Specialist | Database recovery operations |
| Infrastructure Engineer | Cloud infrastructure recovery |
| Application Engineer | Application deployment and verification |
| Security Officer | Security assessment and remediation |
| Communications Lead | Updates to customers and stakeholders |

## Communication Protocols

### Internal Communication

- Primary: Dedicated Slack channel `#dr-active-incident`
- Secondary: Emergency conference bridge
- Updates frequency: Every 30 minutes minimum

### External Communication

- Customer notifications via: Email, status page, in-app notifications
- Pre-approved message templates located in: `docs/communication/templates/`
- Approval chain for external communications:
  1. Incident Commander
  2. Communications Lead
  3. Legal review (if applicable)

## Recovery Procedures

### Critical Scenario: Database Corruption

#### Initial Assessment

```
1. Validate the extent of corruption:
   $ gcloud sql instances describe mobilize-db --format="default(state, settings.databaseFlags)"
   $ gcloud sql connect mobilize-db --user=admin --quiet < scripts/db_integrity_check.sql

2. Isolate affected components:
   - Temporarily disable application write access
   - Enable read-only mode if possible

3. Determine corruption timeframe:
   - Review database logs
   - Identify last known good state
```

#### Recovery Steps

```
1. Stop application services to prevent further damage:
   $ gcloud run services update mobilize-api --no-traffic

2. Identify most recent clean backup:
   $ gcloud sql backups list --instance=mobilize-db --filter="status:SUCCESSFUL" --limit=10

3. Restore database from backup:
   $ gcloud sql instances restore mobilize-db --restore-backup-name=BACKUP_ID

4. Apply transaction logs if available:
   $ gcloud sql instances restore mobilize-db \
     --restore-backup-name=BACKUP_ID \
     --recovery-point-in-time=YYYY-MM-DDTHH:MM:SS.SSSZ

5. Verify data integrity:
   $ gcloud sql connect mobilize-db --user=admin --quiet < scripts/db_validation.sql

6. Restart application services:
   $ gcloud run services update mobilize-api --traffic=100
```

#### Post-Recovery Actions

```
1. Verify application functionality:
   $ curl -X GET https://api.mobilize-crm.com/health | jq

2. Run data consistency checks:
   $ python scripts/data_integrity_check.py

3. Document incident details:
   - Timeline of events
   - Actions taken
   - Root cause analysis
   - Preventive measures
```

### Major Scenario: Regional Outage

#### Initial Assessment

```
1. Confirm regional outage:
   $ gcloud compute regions describe REGION_NAME --format="default(status)"
   
2. Check status of backup region:
   $ gcloud compute regions describe BACKUP_REGION --format="default(status)"

3. Evaluate readiness of disaster recovery environment:
   $ ./scripts/dr_readiness_check.sh BACKUP_REGION
```

#### Recovery Steps

```
1. Activate regional failover:
   $ ./scripts/activate_dr_environment.sh BACKUP_REGION

2. Promote database replica to primary:
   $ gcloud sql instances promote-replica mobilize-db-replica-BACKUP_REGION

3. Update DNS to point to DR environment:
   $ gcloud dns record-sets transaction start --zone=mobilize-dns-zone
   $ gcloud dns record-sets transaction update api.mobilize-crm.com. \
     --type=A --ttl=300 --zone=mobilize-dns-zone \
     --rrdatas=DR_ENVIRONMENT_IP
   $ gcloud dns record-sets transaction execute --zone=mobilize-dns-zone

4. Scale up application services in DR region:
   $ gcloud run services update mobilize-api \
     --region=BACKUP_REGION \
     --min-instances=5 \
     --max-instances=20
```

#### Post-Recovery Actions

```
1. Monitor application performance in DR region:
   $ watch -n 60 "./scripts/check_app_health.sh BACKUP_REGION"

2. Verify data consistency across regions:
   $ python scripts/verify_data_consistency.py PRIMARY_REGION BACKUP_REGION

3. Develop plan for returning to primary region:
   - Estimated timeline
   - Data synchronization strategy
   - Cutover approach
```

### Moderate Scenario: Single Component Failure

#### Component-Specific Recovery

##### API Service Failure

```
1. Check service status:
   $ gcloud run services describe mobilize-api --region=us-central1

2. Review logs for errors:
   $ gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-api" --limit=50

3. Restore service from backup:
   $ gcloud run deploy mobilize-api \
     --image=gcr.io/PROJECT_ID/mobilize-api:LAST_KNOWN_GOOD_VERSION \
     --region=us-central1
```

##### Authentication Service Failure

```
1. Check Firebase Authentication status:
   $ curl -X GET https://status.firebase.google.com/api/v1/status

2. If service is down, enable local authentication fallback:
   $ gcloud run services update mobilize-api \
     --update-env-vars="AUTH_FALLBACK_ENABLED=true"

3. Once resolved, disable fallback:
   $ gcloud run services update mobilize-api \
     --update-env-vars="AUTH_FALLBACK_ENABLED=false"
```

##### Storage Service Failure

```
1. Check GCS bucket status:
   $ gcloud storage buckets describe gs://mobilize-storage

2. If unreachable, enable alternative storage:
   $ gcloud run services update mobilize-api \
     --update-env-vars="USE_BACKUP_STORAGE=true,BACKUP_STORAGE_BUCKET=mobilize-storage-backup"

3. Once resolved, synchronize data and switch back:
   $ gsutil -m rsync -r gs://mobilize-storage-backup gs://mobilize-storage
   $ gcloud run services update mobilize-api \
     --update-env-vars="USE_BACKUP_STORAGE=false"
```

## Security Incident Response

### Ransomware/Data Breach Response

#### Containment

```
1. Isolate affected systems:
   $ gcloud compute firewall-rules create emergency-isolation \
     --direction=INGRESS --priority=0 \
     --action=DENY --rules=all \
     --target-tags=compromised-systems

2. Revoke active credentials:
   $ gcloud iam service-accounts disable backup-service-account@PROJECT_ID.iam.gserviceaccount.com
   $ ./scripts/revoke_all_active_tokens.sh

3. Enable enhanced logging:
   $ gcloud logging sinks create security-incident-sink \
     storage.googleapis.com/security-incident-logs \
     --log-filter="severity>=WARNING"
```

#### Recovery

```
1. Create isolated recovery environment:
   $ ./scripts/create_isolated_recovery_env.sh

2. Restore from last known clean backup:
   $ gcloud sql instances create mobilize-db-recovery \
     --region=us-central1 \
     --database-version=POSTGRES_14 \
     --restore-backup-name=LAST_CLEAN_BACKUP_ID

3. Deploy clean application version:
   $ gcloud run deploy mobilize-api-recovery \
     --image=gcr.io/PROJECT_ID/mobilize-api:VERIFIED_CLEAN_VERSION \
     --region=us-central1 \
     --no-allow-unauthenticated

4. Perform security scan before restoration:
   $ ./scripts/security_scan.sh recovery-environment
```

#### Post-Incident

```
1. Document security incident:
   $ ./scripts/generate_security_incident_report.sh INCIDENT_ID

2. Report to relevant authorities:
   - Follow procedures in docs/security/breach_reporting.md

3. Conduct lessons learned session:
   - Schedule within 1 week of resolution
   - Include all stakeholders
   - Document findings in security posture improvement plan
```

## Business Continuity

### Critical Business Functions

| Function | Maximum Tolerable Downtime | Recovery Time Objective | Recovery Point Objective |
|----------|----------------------------|-------------------------|--------------------------|
| Customer Data Access | 4 hours | 1 hour | 15 minutes |
| User Authentication | 2 hours | 30 minutes | 5 minutes |
| Campaign Management | 8 hours | 2 hours | 1 hour |
| Reporting | 24 hours | 4 hours | 12 hours |

### Manual Workarounds

Document procedures for continuing operations during extended outages:

1. **Customer Data Access**
   - Export daily customer data to secure spreadsheets
   - Provide read-only emergency access portal
   
2. **User Authentication**
   - Maintain emergency access credentials list (secured)
   - Enable local authentication override procedure
   
3. **Campaign Management**
   - Maintain templates for manual campaign launch
   - Train staff on manual campaign execution

## Recovery Testing

### Test Schedule

| Test Type | Frequency | Duration | Participants |
|-----------|-----------|----------|--------------|
| Tabletop Exercise | Monthly | 2 hours | All recovery team members |
| Component Recovery Test | Quarterly | 4 hours | Technical team members |
| Full DR Test | Bi-annually | 8 hours | All recovery team + business stakeholders |

### Test Scenarios

1. **Database Recovery Test**
   - Simulate database corruption
   - Perform backup restoration
   - Validate data integrity
   - Document recovery time

2. **Regional Failover Test**
   - Simulate primary region outage
   - Activate DR environment
   - Validate application functionality
   - Measure actual RTO and RPO

3. **Security Incident Test**
   - Simulate ransomware attack
   - Execute containment procedures
   - Perform clean restoration
   - Validate security controls

## Appendix

### Recovery Resources

#### Scripts and Tools Location

- Recovery scripts: `scripts/disaster_recovery/`
- Infrastructure as Code: `terraform/dr_environment/`
- Validation tools: `tools/validation/`

#### Credentials Access

Emergency credentials are stored in the secure vault:
- Access procedure documented in: `docs/security/emergency_access.md`
- Authorization requires: Incident Commander + Security Officer approval

#### Third-Party Support Contacts

| Vendor | Service | Contact | SLA |
|--------|---------|---------|-----|
| Google Cloud | Infrastructure | support@googlecloud.com / 1-800-XXX-XXXX | 1 hour |
| Datadog | Monitoring | emergency@datadog.com / 1-800-XXX-XXXX | 2 hours |
| Cloudflare | CDN/DNS | enterprise-support@cloudflare.com / 1-800-XXX-XXXX | 30 minutes |

### Recovery Checklist

```
□ Incident declared and team activated
□ Initial assessment completed
□ Recovery strategy determined
□ Stakeholders notified
□ Recovery procedures initiated
□ Progress updates communicated (every 30 min)
□ Recovery completion verified
□ Applications tested and validated
□ Return to normal operations
□ Incident documentation completed
□ Post-incident review scheduled
```

### Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | YYYY-MM-DD | [Author] | Initial document |
| 1.1 | YYYY-MM-DD | [Author] | Updated regional failover procedure |
| 2.0 | YYYY-MM-DD | [Author] | Added security incident response procedures | 