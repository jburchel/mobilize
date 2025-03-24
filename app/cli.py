"""Command line interface for the app."""
import click
from flask.cli import with_appcontext
from app.extensions import db

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
    """Register CLI commands with the app."""
    app.cli.add_command(setup_db)
    app.cli.add_command(setup_main_pipelines_command)
    app.cli.add_command(migrate_contacts_command) 