import click
from database.crud import recreate_database

# Command for removing all data entries in database, tables will still remain.


@click.command()
def cli():
    """Deletes all database entries"""
    
    print("Are you sure you want to delete all data entries in the database?")
    if input("Enter y/n: ") == "y":
        recreate_database()
