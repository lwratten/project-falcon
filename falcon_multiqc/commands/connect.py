import click
import re
import sys
from getpass import getpass
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
from database.models import get_tables

"""
Connect command allows user to modify the config.py DATABASE_URI
with their username, password and database name.
If the user has not yet made a falcon_multiqc database,
this command allows them to make a new one.
"""

# function to modify the config.py file with a new DATABASE_URI for the current user
def create_config(username, password, port, uri, database):
    with open("database/config.py", "w") as config_file:
        config_file.write("### config.py ###\n\n")
        if uri:
            config_file.write(f'DATABASE_URI = "postgres+psycopg2://{uri[0]}:{uri[1]}@{uri[2]}:{uri[3]}/{uri[4]}"')
        else:
            config_file.write(f'DATABASE_URI = "postgres+psycopg2://{username}:{password}@localhost:{port}/{database}"')


@click.command()
@click.option(
    "-u",
    "--uri",
    type=click.STRING,
    required=False,
    help="Enter complete DATABASE_URI (e.g. 'postgres+psycopg2://USERNAME:PASSWORD@IP_ADDRESS:PORT/DATABASE_NAME') - Note, this can create a new db as well",
)
def cli(uri):
    """Connects the user to a postgres database, creates new database one doesn't exist"""

    username, password, port, database = (None, None, None, None)
    while True:
        if not uri:
            click.echo("Please enter the username and password for your postgres server:")
            username = click.prompt("Enter username (e.g. postgres)")
            password = getpass("Enter password: ")
            port = click.prompt("Enter port number for your server: ")
        try:
            if uri:
                uri = re.search("//(.+):(.+)@(localhost|(?:[0-9]{1,3}\.){3}[0-9]{1,3}):(\d+)/(.+)$", uri)
                if not uri:
                    # The format string entered as uri is incorrect so throw a meaningful error
                    click.echo("Error: Invalid URI inputted, accepted URI format is postgres+psycopg2://USERNAME:PASSWORD@IP_ADDRESS:0/DATABASE_NAME\nExiting falcon_multiqc...")
                    sys.exit(1)
                uri = uri.groups()  # split up the match into an array
                login_engine = create_engine(f"postgres+psycopg2://{uri[0]}:{uri[1]}@{uri[2]}:{uri[3]}")
            else:
                login_engine = create_engine(f"postgres+psycopg2://{username}:{password}@localhost:{port}")
            login_engine.connect().close()  # try to form a connection with db using username/password and immediately close - raises OperationaError if wrong
            break
        except OperationalError:
            if uri:
                click.echo("Error: username or password could not connect to postgres server\nExiting falcon_multiqc...")
                sys.exit(1)
            click.echo("Username or password could not connect to postgres server\n")
    with login_engine.connect() as conn:
        databases = list(conn.execute("SELECT datname FROM pg_database WHERE datistemplate = false;"))  # queries postgreSQL for list of avaliable databases #.scalar() is None
        if not uri:
            click.echo(f"\nAvaliable databases under {username} user are:")
            [click.echo(f"{d[0]}") for d in databases]

        while True:
            if not uri:
                database = click.prompt("\nEnter database name to connect, or enter new name to create a new falcon_multiqc database")
            if (database,) in databases or (uri and (uri[4],)) in databases:
                if uri:
                    check_db_engine = create_engine(f"postgres+psycopg2://{uri[0]}:{uri[1]}@{uri[2]}:{uri[3]}/{uri[4]}")
                else:
                    check_db_engine = create_engine(f"postgres+psycopg2://{username}:{password}@localhost:{port}/{database}")
                falcon_multiqc_schema = get_tables()  # load current falcon_multiqc schema
                inspector = inspect(check_db_engine)

                if len([t for t in falcon_multiqc_schema if t in inspector.get_table_names()]) != len(falcon_multiqc_schema):  # checks whether selected db has falcon_multiqc schema
                    if uri:
                        click.echo("\n===\nWarning, entered database is not a falcon_multiqc database\n===\n\nExiting falcon_multiqc...")
                        sys.exit(1)
                    click.echo("\n===\nWarning, selected database is not a falcon_multiqc database, please try again or create a new database\n===")
                    continue
                create_config(username, password, port, uri, database)  # re-create config file with proper connection URL
                check_db_engine.dispose()
            else:
                """Creates a new database"""
                click.echo("Creating new database...")
                create_config(username, password, port, uri, database)
                conn.execute("commit")  # databases cannot be created inside transactions, this line will close the previous transaction
                conn.execute(f"create database {uri[4]}") if uri else conn.execute(f"create database {database}")  # create an empty database
                from database.crud import create_database

                create_database()  # populate the database with tables
                click.echo("Database has been created!")
            break
        click.echo(
            f"You are now connected to database {database}!\nUse the URI: 'postgres+psycopg2://{username}:{password}@localhost:{port}/{database}' to log in using -u option from now on"
        ) if not uri else click.echo(f"You are now connected to database {uri[4]}!")
    login_engine.dispose()
