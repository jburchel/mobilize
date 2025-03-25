"""Command line interface for the app."""
import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import User, Contact
import json
import os
from datetime import datetime

@click.command("setup-db")
@with_appcontext
def setup_db():
    """Initialize the database."""
    db.create_all()
    click.echo("Database tables created.")

@click.command("setup-main-pipelines")
@with_appcontext
def setup_main_pipelines_command():
    """Set up the main pipelines for people and churches."""
    from app.utils.setup_main_pipelines import setup_main_pipelines
    setup_main_pipelines()
    click.echo("Main pipelines setup complete.")

@click.command("migrate-contacts")
@with_appcontext
def migrate_contacts_command():
    """Migrate existing contacts to the main pipelines."""
    from app.utils.migrate_contacts_to_main_pipeline import migrate_contacts_to_main_pipelines
    migrate_contacts_to_main_pipelines()
    click.echo("Contact migration to main pipelines complete.")

def register_commands(app):
    """Register custom Flask CLI commands."""
    app.cli.add_command(reset_db_command)
    app.cli.add_command(seed_db_command)
    app.cli.add_command(run_automations_command)

@click.command("reset-db")
@with_appcontext
def reset_db_command():
    """Clear existing data and create new tables."""
    if click.confirm("This will delete all data in the database. Continue?"):
        db.drop_all()
        db.create_all()
        click.echo("Database tables reset!")

@click.command("seed-db")
@click.option("--sample-data", is_flag=True, help="Add sample data to the database.")
@with_appcontext
def seed_db_command(sample_data):
    """Seed the database with initial data."""
    # Create roles if they don't exist - in this app, roles are strings in the User model
    click.echo("Setting up user roles...")
    
    if sample_data:
        from app.models import Office, Person, Church, Task
        
        # Create sample offices
        main_office = Office(name="Main Office", address="123 Main St", is_active=True)
        db.session.add(main_office)
        db.session.flush()  # To get the ID
        
        # Create admin user
        admin = User.query.filter_by(email="admin@example.com").first()
        if not admin:
            admin = User(
                first_name="Admin",
                last_name="User",
                username="admin",
                email="admin@example.com",
                is_active=True,
                role="super_admin",
                office_id=main_office.id
            )
            admin.set_password("password")
            db.session.add(admin)
        
        # Add some contacts
        for i in range(10):
            person = Person(
                first_name=f"Person{i}",
                last_name=f"Sample{i}",
                email=f"person{i}@example.com",
                phone=f"555-123-{i:04d}",
                type="person",
                office_id=main_office.id
            )
            db.session.add(person)
        
        for i in range(5):
            church = Church(
                name=f"Church {i}",
                email=f"church{i}@example.com",
                phone=f"555-987-{i:04d}",
                type="church",
                office_id=main_office.id
            )
            db.session.add(church)
            
        # Create some tasks
        contacts = Contact.query.all()
        for i, contact in enumerate(contacts):
            if i < 5:  # Just create tasks for a few contacts
                task = Task(
                    title=f"Follow up with {contact.get_name()}",
                    description=f"This is a sample task for {contact.get_name()}",
                    contact_id=contact.id,
                    office_id=main_office.id,
                    due_date=datetime.utcnow(),
                    is_completed=False
                )
                db.session.add(task)
        
        # Create pipeline data
        from app.models import Pipeline, PipelineStage
        
        # Create main people pipeline
        people_pipeline = Pipeline(
            name="People Pipeline",
            description="Main pipeline for managing people contacts",
            pipeline_type="people",
            office_id=main_office.id,
            is_main_pipeline=True
        )
        db.session.add(people_pipeline)
        db.session.flush()
        
        # Add stages to people pipeline
        stages = [
            {"name": "New Contact", "order": 1, "color": "#3498db", "auto_move_days": 7, "auto_reminder": True},
            {"name": "Initial Contact", "order": 2, "color": "#2ecc71", "auto_reminder": True},
            {"name": "Meeting Scheduled", "order": 3, "color": "#f1c40f", "auto_task_template": json.dumps({
                "title": "Follow up after meeting",
                "description": "Send a follow-up email after the scheduled meeting",
                "days_to_complete": 2,
                "priority": "HIGH"
            })},
            {"name": "Follow Up", "order": 4, "color": "#e67e22", "auto_reminder": True},
            {"name": "Converted", "order": 5, "color": "#27ae60"}
        ]
        
        for stage_data in stages:
            stage = PipelineStage(
                pipeline_id=people_pipeline.id,
                name=stage_data["name"],
                order=stage_data["order"],
                color=stage_data["color"],
                is_active=True,
                auto_move_days=stage_data.get("auto_move_days"),
                auto_reminder=stage_data.get("auto_reminder", False),
                auto_task_template=stage_data.get("auto_task_template")
            )
            db.session.add(stage)
        
        db.session.commit()
        click.echo("Sample data created!")
    
    click.echo("Database seeded successfully!")

@click.command("run-automations")
@click.option("--dry-run", is_flag=True, help="Show what would happen without making changes.")
@with_appcontext
def run_automations_command(dry_run):
    """Run automated tasks like pipeline automations."""
    click.echo("Running automations...")
    
    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made")
    
    # Run pipeline automations
    from app.services.pipeline_automation import run_pipeline_automations
    
    try:
        if dry_run:
            # Just log what would happen
            click.echo("Would run pipeline automations:")
            from app.services.pipeline_automation import (
                process_automatic_movements,
                process_automatic_reminders,
                process_automatic_tasks
            )
            
            # Get counts without committing changes
            contacts_to_move = process_automatic_movements()
            click.echo(f" - Would move {contacts_to_move} contacts")
            
            reminders_to_send = process_automatic_reminders()
            click.echo(f" - Would send {reminders_to_send} reminders")
            
            tasks_to_create = process_automatic_tasks()
            click.echo(f" - Would create {tasks_to_create} tasks")
            
            # Rollback any changes made during dry run
            db.session.rollback()
        else:
            # Actually run the automations
            result = run_pipeline_automations()
            click.echo(f"Pipeline automations completed:")
            click.echo(f" - Moved {result['contacts_moved']} contacts")
            click.echo(f" - Sent {result['reminders_sent']} reminders")
            click.echo(f" - Created {result['tasks_created']} tasks")
    except Exception as e:
        click.echo(f"Error running automations: {str(e)}", err=True)
        return
    
    click.echo("Automations completed!") 