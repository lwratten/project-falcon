import click
from database.crud import recreate_database

# Command for removing all data entries in database, tables will still remain.


@click.command()
def cli():
    """Deletes all database entries"""
    
    click.echo("Are you sure you want to delete all data entries in the database?")
    if click.prompt("Enter y/n: ") == "y":
        recreate_database()
