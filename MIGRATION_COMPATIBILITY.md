# PostgreSQL Migration Compatibility

## Overview

This document outlines the PostgreSQL compatibility for migrations in the Mobilize CRM application. Our analysis has identified several potential compatibility issues when migrating from SQLite to PostgreSQL.

## Migration Analysis Summary

A comprehensive analysis of the migration files revealed the following:

- **Total migration files analyzed**: 27
- **Files with compatibility issues**: 12
- **Total potential issues found**: 137

## Main Compatibility Issues

1. **DateTime Column Type**: 
   - The most common issue is the use of SQLite-specific `DateTime()` function which needs to be replaced with PostgreSQL's `TIMESTAMP WITHOUT TIME ZONE`.
   - This affects 96% of the identified issues, appearing in multiple migration files.

2. **AUTOINCREMENT Syntax**:
   - SQLite uses `AUTOINCREMENT`, while PostgreSQL uses `SERIAL` or `IDENTITY` for auto-incrementing columns.
   - Found in the production-ready schema migration file.

## Latest Migration Analysis

### Migration: `pipeline_stage_history_fix_patched.py`

The latest migration performs the following operations:

1. **Schema Changes**:
   - Adds `created_at` column (DateTime) to `pipeline_stage_history` table
   - Adds `created_by_id` column (Integer) to `pipeline_stage_history` table if it doesn't exist
   - Creates a foreign key constraint from `created_by_id` to `users.id`

2. **Data Migration**:
   - Updates `created_at` with values from `moved_at` where available
   - Sets `created_at` to current timestamp for any NULL values
   - Copies data from `moved_by_user_id` to `created_by_id` where available

3. **SQL Commands Generated**:
   ```sql
   ALTER TABLE pipeline_stage_history ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE;
   ALTER TABLE pipeline_stage_history ADD COLUMN created_by_id INTEGER;
   ALTER TABLE pipeline_stage_history ADD CONSTRAINT fk_pipeline_stage_history_created_by_id_users FOREIGN KEY (created_by_id) REFERENCES users (id);
   UPDATE pipeline_stage_history SET created_at = moved_at WHERE moved_at IS NOT NULL;
   UPDATE pipeline_stage_history SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
   UPDATE pipeline_stage_history SET created_by_id = moved_by_user_id WHERE moved_by_user_id IS NOT NULL;
   ```

## Mitigation Strategy

To ensure smooth migration to PostgreSQL, the following steps are recommended:

1. **DateTime/Timestamp Issues**:
   - Modify all migrations to use PostgreSQL-compatible timestamp types by ensuring column definitions use `sa.DateTime()` consistently.
   - When creating schema from scratch, use PostgreSQL-specific timestamp types directly.

2. **Autoincrement Issues**:
   - Replace any SQLite `AUTOINCREMENT` with PostgreSQL-compatible sequences or `SERIAL` type.
   - For explicit schema creation, use `sa.Integer()` with `primary_key=True` which SQLAlchemy translates appropriately for each database.

3. **Testing Approach**:
   - Use the provided `postgres_migration_tester.py` script to identify and fix specific issues.
   - For any file with reported issues, review and update the SQLite-specific syntax with PostgreSQL-compatible equivalents.
   - Test each migration against a PostgreSQL database before applying to production.

## Impact Assessment

The identified issues have varying levels of impact:

1. **High Impact**: 
   - Datetime format differences may cause data type errors during migration
   - Autoincrement syntax differences affect table creation

2. **Medium Impact**:
   - Most other SQLite-specific functions can be adapted when encountered

3. **Low Impact**:
   - Minor syntax differences that could be automatically addressed by SQLAlchemy

## Recommended Testing Approach

Before applying to production:

1. **Verify Schema**:
   - Confirm the database structure in PostgreSQL using the included migration tester
   - Check if any columns already exist to prevent duplicate column errors

2. **Test Data Migration**:
   - Run a test migration on a copy of the production data
   - Validate that data is correctly transferred between columns
   - Verify data types are correctly translated during the process

3. **Rollback Plan**:
   - The downgrade functions should work as expected but test them specifically
   - Test the rollback on a test database before applying to production

## Conclusion

While there are compatibility issues between SQLite and PostgreSQL in the current migration files, most are related to DateTime type specifications that SQLAlchemy can handle internally. With proper testing and the recommended mitigations, the migration to PostgreSQL should proceed successfully. The most critical migration file (`pipeline_stage_history_fix_patched.py`) has clean SQL commands that should work on PostgreSQL without modification. 