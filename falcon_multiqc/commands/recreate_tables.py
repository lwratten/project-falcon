import click
from database.crud import recreate_database

# Command for initalizing database.
@click.command()
def cli():
    """Creates new database tables, overwriting the last."""
    recreate_database()
    click.echo("Database has been created!")
