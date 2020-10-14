import click
from database.crud import create_database, recreate_database

# Command for initalizing database.


@click.command()
@click.option("-d", "--destroy", is_flag=True, help="Destroy the old database (drop all tables)")
def cli(destroy):
    """Creates a new database"""

    if (destroy):
        recreate_database()
    else:
        create_database()
