import click
from database.crud import recreate_database

# Command for initalizing database.
@click.command()
def cli():
    """Creates new database tables, overwriting the last."""
    if click.confirm('Are you sure you want to recreate your tables (all stored data wil be lost)?'):
        recreate_database()
        click.echo("Database has been created!")
    else:
        click.echo("Recreate tables has been aborted.")
