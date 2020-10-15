import click
from database.crud import create_database

# Command for initalizing database.


@click.command()
def cli():
    """Creates a new database"""
    
    create_database()
    print("Database has been created!")
    #TODO check to see if tables already exist and prompt user if they already do
