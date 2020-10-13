import click
from database.crud import create_database

# Command for initalizing database.


@click.command()
def cli():
    """Creates a new database"""
    create_database()
