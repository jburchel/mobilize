# Supabase PostgreSQL Connection Notes

This document provides key information about connecting to our Supabase PostgreSQL database for the Mobilize CRM application.

## Connection String Formats

Supabase offers multiple connection string formats, but we found that the **Supavisor Connection Pooler** provides the most reliable connection for our application:

```
postgresql://postgres.fwnitauuyzxnsvgsbrzr:RV4QOygx0LpqOjzx@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

Other connection formats we tried but found less reliable:

1. **Direct Connection**:
   ```
   postgresql://postgres:Fruitin2025!@db.fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres
   ```

2. **Without `db.` prefix**:
   ```
   postgresql://postgres:Fruitin2025!@fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres
   ```

## Connection Testing Results

| Connection Method | Result | Notes |
|-------------------|--------|-------|
| Direct Connection | ❌ Timeout | Can't reach port 5432 directly |
| Without `db.` prefix | ❌ Timeout | Can't reach port 5432 directly |
| Supavisor Connection Pooler | ✅ Success | Connects successfully with correct credentials |

## SQLAlchemy 2.0 Compatibility

When working with direct SQL in migration files, make sure to wrap SQL strings with `text()` from SQLAlchemy:

```python
from sqlalchemy import text

# Instead of:
session.execute("UPDATE table SET column = value")

# Use:
session.execute(text("UPDATE table SET column = value"))
```

This is necessary to comply with SQLAlchemy 2.0's stricter SQL handling.

## Migration Testing

To test migrations without actually applying them:

1. Use the `pg_migration_test_final.py` script to:
   - Test connectivity to the database
   - Generate SQL statements that would be executed
   - Validate that database tables and columns exist

2. Important flags for migration commands:
   - `--sql`: Generate SQL without executing it
   - `--autogenerate`: Create a migration based on model changes

## Troubleshooting

- **Connection Timeout**: Ensure you're using the Supavisor Connection Pooler URL
- **Authentication Errors**: Verify the correct password is being used (currently `RV4QOygx0LpqOjzx`)
- **IP Restrictions**: Check if your IP is allowed in Supabase dashboard
- **SQLAlchemy Errors**: Ensure SQL strings are wrapped with `text()`

## Production Environment Configuration

The production environment file (`.env.production`) has been updated to use the Supavisor Connection Pooler URL for reliable database connectivity. 