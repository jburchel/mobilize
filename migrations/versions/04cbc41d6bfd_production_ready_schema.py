"""Production ready schema

Revision ID: 04cbc41d6bfd
Revises: b604f5030685
Create Date: 2025-04-17 16:18:16.258410

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '04cbc41d6bfd'
down_revision = 'b604f5030685'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('churches', schema=None) as batch_op:
        batch_op.alter_column('virtuous',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('church_pipeline',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('priority',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('assigned_to',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('source',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.drop_column('associate_pastor_name')

    with op.batch_alter_table('communications', schema=None) as batch_op:
        batch_op.alter_column('google_meet_link',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)
        batch_op.alter_column('google_calendar_event_id',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.drop_index('idx_communications_date')
        batch_op.drop_index('idx_communications_person_id')
        batch_op.drop_index('idx_communications_user_id')

    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.alter_column('type',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
        batch_op.alter_column('date_created',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('date_modified',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('has_conflict',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.drop_index('idx_contacts_email')
        batch_op.drop_index('idx_contacts_google_id')
        batch_op.drop_index('idx_contacts_name')
        batch_op.drop_index('idx_contacts_office_id')
        batch_op.drop_index('idx_contacts_type')
        batch_op.drop_index('idx_contacts_user_id')

    with op.batch_alter_table('email_campaigns', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('email_signatures', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('email_templates', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('email_tracking', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('google_tokens', schema=None) as batch_op:
        batch_op.alter_column('scopes',
               existing_type=sqlite.JSON(),
               type_=sa.Text(),
               existing_nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('offices', schema=None) as batch_op:
        batch_op.alter_column('timezone',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
        batch_op.alter_column('is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('calendar_sync_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('meet_integration_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('drive_integration_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('people', schema=None) as batch_op:
        batch_op.alter_column('is_primary_contact',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('virtuous',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('marital_status',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=50),
               existing_nullable=True)
        batch_op.alter_column('occupation',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.alter_column('employer',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.alter_column('facebook',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.alter_column('twitter',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.alter_column('linkedin',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.alter_column('instagram',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.alter_column('website',
               existing_type=sa.TEXT(),
               type_=sa.String(length=200),
               existing_nullable=True)
        batch_op.alter_column('last_contact',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
        batch_op.alter_column('people_pipeline',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('priority',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
        batch_op.alter_column('assigned_to',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
        batch_op.alter_column('source',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
        batch_op.drop_column('date_of_birth')

    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('pipeline_contacts', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=False,
               autoincrement=True)
        batch_op.drop_index('idx_pipeline_contacts_contact_id')
        batch_op.drop_index('idx_pipeline_contacts_current_stage_id')
        batch_op.drop_index('idx_pipeline_contacts_pipeline_id')

    with op.batch_alter_table('pipeline_stage_history', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['created_by_id'], ['id'])
        batch_op.drop_column('moved_by_user_id')
        batch_op.drop_column('moved_at')
        batch_op.drop_column('is_automated')

    with op.batch_alter_table('pipeline_stages', schema=None) as batch_op:
        batch_op.drop_index('idx_pipeline_stages_pipeline_id')
        batch_op.drop_column('is_active')

    with op.batch_alter_table('pipelines', schema=None) as batch_op:
        batch_op.alter_column('pipeline_type',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=True,
               existing_server_default=sa.text("'people'"))
        batch_op.alter_column('office_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('is_main_pipeline',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('0'))
        batch_op.drop_column('is_active')

    with op.batch_alter_table('role_permissions', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.alter_column('priority',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.drop_index('idx_tasks_created_by')
        batch_op.drop_index('idx_tasks_due_date')
        batch_op.drop_index('idx_tasks_owner_id')
        batch_op.drop_index('idx_tasks_person_id')
        batch_op.drop_column('completed_at')
        batch_op.drop_column('reminder_sent')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('first_login',
               existing_type=sa.DATETIME(),
               type_=sa.Boolean(),
               nullable=False,
               existing_server_default=sa.text('(NULL)'))
        batch_op.alter_column('google_calendar_sync',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('google_meet_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('email_sync_contacts_only',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('0'))
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.create_foreign_key(None, 'roles', ['role_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('email_sync_contacts_only',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('0'))
        batch_op.alter_column('google_meet_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('google_calendar_sync',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('first_login',
               existing_type=sa.Boolean(),
               type_=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(NULL)'))
        batch_op.alter_column('is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reminder_sent', sa.BOOLEAN(), server_default=sa.text('0'), nullable=True))
        batch_op.add_column(sa.Column('completed_at', sa.DATETIME(), nullable=True))
        batch_op.create_index('idx_tasks_person_id', ['person_id'], unique=False)
        batch_op.create_index('idx_tasks_owner_id', ['owner_id'], unique=False)
        batch_op.create_index('idx_tasks_due_date', ['due_date'], unique=False)
        batch_op.create_index('idx_tasks_created_by', ['created_by'], unique=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('priority',
               existing_type=sa.VARCHAR(),
               nullable=True)

    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('role_permissions', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('pipelines', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.BOOLEAN(), nullable=True))
        batch_op.alter_column('is_main_pipeline',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('0'))
        batch_op.alter_column('office_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('pipeline_type',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=True,
               existing_server_default=sa.text("'people'"))

    with op.batch_alter_table('pipeline_stages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.BOOLEAN(), nullable=True))
        batch_op.create_index('idx_pipeline_stages_pipeline_id', ['pipeline_id'], unique=False)

    with op.batch_alter_table('pipeline_stage_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_automated', sa.BOOLEAN(), nullable=True))
        batch_op.add_column(sa.Column('moved_at', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('moved_by_user_id', sa.INTEGER(), nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['moved_by_user_id'], ['id'])

    with op.batch_alter_table('pipeline_contacts', schema=None) as batch_op:
        batch_op.create_index('idx_pipeline_contacts_pipeline_id', ['pipeline_id'], unique=False)
        batch_op.create_index('idx_pipeline_contacts_current_stage_id', ['current_stage_id'], unique=False)
        batch_op.create_index('idx_pipeline_contacts_contact_id', ['contact_id'], unique=False)
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=True,
               autoincrement=True)

    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('people', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date_of_birth', sa.DATE(), nullable=True))
        batch_op.alter_column('source',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
        batch_op.alter_column('assigned_to',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
        batch_op.alter_column('priority',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
        batch_op.alter_column('people_pipeline',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
        batch_op.alter_column('last_contact',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('website',
               existing_type=sa.String(length=200),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('instagram',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('linkedin',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('twitter',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('facebook',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('employer',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('occupation',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('marital_status',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=100),
               existing_nullable=True)
        batch_op.alter_column('virtuous',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('is_primary_contact',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    with op.batch_alter_table('offices', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('drive_integration_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('meet_integration_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('calendar_sync_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('timezone',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)

    with op.batch_alter_table('google_tokens', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('scopes',
               existing_type=sa.Text(),
               type_=sqlite.JSON(),
               existing_nullable=True)

    with op.batch_alter_table('email_tracking', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('email_templates', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('email_signatures', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('email_campaigns', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.create_index('idx_contacts_user_id', ['user_id'], unique=False)
        batch_op.create_index('idx_contacts_type', ['type'], unique=False)
        batch_op.create_index('idx_contacts_office_id', ['office_id'], unique=False)
        batch_op.create_index('idx_contacts_name', ['first_name', 'last_name'], unique=False)
        batch_op.create_index('idx_contacts_google_id', ['google_contact_id'], unique=False)
        batch_op.create_index('idx_contacts_email', ['email'], unique=False)
        batch_op.alter_column('has_conflict',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('date_modified',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('date_created',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('type',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)

    with op.batch_alter_table('communications', schema=None) as batch_op:
        batch_op.create_index('idx_communications_user_id', ['user_id'], unique=False)
        batch_op.create_index('idx_communications_person_id', ['person_id'], unique=False)
        batch_op.create_index('idx_communications_date', ['date'], unique=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('google_calendar_event_id',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('google_meet_link',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=True)

    with op.batch_alter_table('churches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('associate_pastor_name', sa.VARCHAR(length=100), nullable=True))
        batch_op.alter_column('source',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('assigned_to',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('priority',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('church_pipeline',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('virtuous',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    # ### end Alembic commands ###
