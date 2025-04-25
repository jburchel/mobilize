
# PostgreSQL Migration Compatibility Report
Generated: 2025-04-21 15:41:29

## Summary
- Total migration files analyzed: 27
- Files with issues: 12
- Total potential issues found: 137

## Detailed Analysis

### 00a6f3565d53_replace_reminder_booleans_with_reminder_.py
**Revision**: 00a6f3565d53
**Down Revision**: ab1e0d1b31aa
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 3
- drop_column: 3

**No issues detected**

---

### 04cbc41d6bfd_production_ready_schema.py
**Revision**: 04cbc41d6bfd
**Down Revision**: b604f5030685
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 9
- drop_column: 9
- create_index: 17
- drop_index: 17
- create_foreign_key: 3
- drop_constraint: 3

**Direct SQL Commands** (9):
1. `'people'`
2. `0`
3. `(NULL)`
4. `0`
5. `0`
6. `(NULL)`
7. `0`
8. `0`
9. `'people'`

**Potential Issues** (64):
- [high] sqlite_specific: `autoincrement`
- [high] sqlite_specific: `autoincrement`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`

---

### 078ff034365a_add_owner_id_to_task_model.py
**Revision**: 078ff034365a
**Down Revision**: 1593af608f53
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 1
- drop_column: 1
- create_foreign_key: 1
- drop_constraint: 1

**No issues detected**

---

### 1593af608f53_add_owner_id_to_communication_model.py
**Revision**: 1593af608f53
**Down Revision**: None
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 1
- drop_column: 1
- create_foreign_key: 2
- drop_constraint: 2

**No issues detected**

---

### 2bf46cf32aa0_add_office_id_to_communication_model.py
**Revision**: 2bf46cf32aa0
**Down Revision**: 078ff034365a
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 1
- drop_column: 1
- create_foreign_key: 1
- drop_constraint: 1

**No issues detected**

---

### 4cb401521a9e_add_is_primary_contact_to_person_and_.py
**Revision**: 4cb401521a9e
**Down Revision**: 00a6f3565d53
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 5
- drop_column: 5
- create_foreign_key: 1
- drop_constraint: 1

**Potential Issues** (2):
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`

---

### 4e0db47e268c_update_task_model_for_task_management_ui.py
**Revision**: 4e0db47e268c
**Down Revision**: bbda44b09940
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 6
- drop_column: 7
- create_foreign_key: 2
- drop_constraint: 2

**Potential Issues** (1):
- [high] sqlite_specific: `DateTime()`

---

### 54265a913aab_merge_multiple_heads.py
**Revision**: 54265a913aab
**Down Revision**: ('add_google_meet_link', 'eeb2b80b5f20', 'pipeline_stage_history_fix')
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:

**No issues detected**

---

### 5be09d8bc98a_add_image_and_preferred_contact_method_.py
**Revision**: 5be09d8bc98a
**Down Revision**: c6b19f008037
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 9
- drop_column: 9
- create_foreign_key: 1
- drop_constraint: 1

**Potential Issues** (4):
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`

---

### 811e9744caca_add_additional_church_fields_from_old_.py
**Revision**: 811e9744caca
**Down Revision**: a85c9265937c
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 20
- drop_column: 20

**No issues detected**

---

### 8ed80b7eaa73_.py
**Revision**: 8ed80b7eaa73
**Down Revision**: ('54265a913aab', 'add_roles_perms')
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:

**No issues detected**

---

### 9761ea2e6b58_add_person_id_to_users_table.py
**Revision**: 9761ea2e6b58
**Down Revision**: 4cb401521a9e
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 1
- drop_column: 1
- create_foreign_key: 1
- drop_constraint: 1

**No issues detected**

---

### a85c9265937c_add_additional_person_fields_from_old_.py
**Revision**: a85c9265937c
**Down Revision**: 5be09d8bc98a
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 12
- drop_column: 12
- create_foreign_key: 1
- drop_constraint: 1

**Potential Issues** (2):
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`

---

### ab1e0d1b31aa_rename_person_role_to_church_role_for_.py
**Revision**: ab1e0d1b31aa
**Down Revision**: 811e9744caca
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 7
- drop_column: 7
- create_foreign_key: 1
- drop_constraint: 1

**Potential Issues** (2):
- [high] sqlite_specific: `DATETIME()`
- [high] sqlite_specific: `DATETIME()`

---

### add_google_meet_link.py
**Revision**: add_google_meet_link
**Down Revision**: None
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 2
- drop_column: 2

**No issues detected**

---

### add_main_pipeline_fields.py
**Revision**: add_main_pipeline_fields
**Down Revision**: None
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 2
- drop_column: 2

**No issues detected**

---

### add_missing_person_fields.py
**Revision**: add_missing_person_fields
**Down Revision**: 54265a913aab
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 23
- drop_column: 23

**Potential Issues** (2):
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`

---

### add_roles_and_permissions.py
**Revision**: add_roles_perms
**Down Revision**: eeb2b80b5f20
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 1
- drop_column: 1
- create_table: 2
- drop_table: 2
- create_foreign_key: 1
- drop_constraint: 1

**Direct SQL Commands** (4):
1. `INSERT INTO roles (name, description, created_at, updated_at) VALUES ('super_admin`
2. `INSERT INTO roles (name, description, created_at, updated_at) VALUES ('office_admin`
3. `INSERT INTO roles (name, description, created_at, updated_at) VALUES ('standard_user`
4. `INSERT INTO roles (name, description, created_at, updated_at) VALUES ('limited_user`

**Potential Issues** (4):
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`

---

### add_scopes_to_google_tokens.py
**Revision**: add_scopes_to_google_tokens
**Down Revision**: 8ed80b7eaa73
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:

**No issues detected**

---

### b604f5030685_merge_heads.py
**Revision**: b604f5030685
**Down Revision**: ('add_missing_person_fields', 'add_scopes_to_google_tokens')
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:

**No issues detected**

---

### bbda44b09940_add_user_id_to_contact_model.py
**Revision**: bbda44b09940
**Down Revision**: 2bf46cf32aa0
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 1
- drop_column: 1
- create_foreign_key: 1
- drop_constraint: 1

**No issues detected**

---

### c6b19f008037_add_google_sync_columns_to_contacts.py
**Revision**: c6b19f008037
**Down Revision**: 4e0db47e268c
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- create_foreign_key: 1

**No issues detected**

---

### eeb2b80b5f20_.py
**Revision**: eeb2b80b5f20
**Down Revision**: ('9761ea2e6b58', 'pipeline_migration')
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:

**No issues detected**

---

### modified_pg_migration.py
**Revision**: modified_pg_migration
**Down Revision**: 04cbc41d6bfd
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- create_table: 20
- drop_table: 20
- create_index: 2
- drop_index: 2

**Potential Issues** (47):
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`

---

### pipeline_migration.py
**Revision**: pipeline_migration
**Down Revision**: 4cb401521a9e
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- create_table: 4
- drop_table: 4

**Potential Issues** (7):
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`
- [high] sqlite_specific: `DateTime()`

---

### pipeline_stage_history_fix.py
**Revision**: pipeline_stage_history_fix
**Down Revision**: add_main_pipeline_fields
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 2
- drop_column: 2
- create_foreign_key: 1
- drop_constraint: 1

**Direct SQL Commands** (3):
1. `UPDATE pipeline_stage_history SET created_at = moved_at WHERE moved_at IS NOT NULL`
2. `UPDATE pipeline_stage_history SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL`
3. `UPDATE pipeline_stage_history SET created_by_id = moved_by_user_id WHERE moved_by_user_id IS NOT NULL`

**Potential Issues** (1):
- [high] sqlite_specific: `DateTime()`

---

### pipeline_stage_history_fix_patched.py
**Revision**: pipeline_stage_history_fix
**Down Revision**: add_main_pipeline_fields
**Has Upgrade**: True
**Has Downgrade**: True

**Alembic Operations**:
- add_column: 2
- drop_column: 2
- create_foreign_key: 1
- drop_constraint: 1

**Direct SQL Commands** (3):
1. `UPDATE pipeline_stage_history SET created_at = moved_at WHERE moved_at IS NOT NULL`
2. `UPDATE pipeline_stage_history SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL`
3. `UPDATE pipeline_stage_history SET created_by_id = moved_by_user_id WHERE moved_by_user_id IS NOT NULL`

**Potential Issues** (1):
- [high] sqlite_specific: `DateTime()`

---

