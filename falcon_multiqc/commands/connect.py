import click
from getpass import getpass
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError

# connect command allows user to modify the config.py DATABASE_URI with their username, password and database name
# if the user has not yet made a falcon_multiqc database, this command allows them to make a new one

#global list 
falcon_multiqc_schema = ['cohort', 'patient', 'batch', 'sample', 'PatientBatch', 'raw_data']

# function to modify the config.py file with a new DATABASE_URI for the current user
def create_config(username, password, server_address, database):
    with open("database/config.py", 'w') as config_file:
        config_file.write("### config.py ###\n\n")
        if server_address:
            config_file.write(f'DATABASE_URI = "postgres+psycopg2://{username}:{password}@{server_address[0]}:{server_address[1]}/{database}"')
        else:
            config_file.write(f'DATABASE_URI = "postgres+psycopg2://{username}:{password}@localhost:5432/{database}"')

@click.command()
@click.option("-a", "--server_address", type=click.STRING, required=False, help="Enter IPV4 and port for postgres server (e.g. 192.0.2.1 5432")
def cli(server_address):
    """Connects the user to a postgres database, creates new database one doesn't exist"""

    click.echo("Please enter the username and password for your postgres server\n")
    while True:
        username = click.prompt("Enter username (e.g. postgres)")
        password = getpass("Enter password: ")
        try:
            if server_address:
                server_address = server_address.split()
                login_engine = create_engine(f'postgres+psycopg2://{username}:{password}@{server_address[0]}:{server_address[1]}')
            else:
                login_engine = create_engine(f'postgres+psycopg2://{username}:{password}@localhost:5432')
            login_engine.connect().close() # try to form a connection with db using username/password and immediately close - raises OperationaError if wrong   
            break
        except OperationalError: 
            click.echo("Username or password could not connect to postgres server\n")
    with login_engine.connect() as conn:
        databases = list(conn.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")) # queries postgreSQL for list of avaliable databases #.scalar() is None
        click.echo(f'\nAvaliable databases under {username} user are:')
        [click.echo(f'{d[0]}') for d in databases]

        while True:
            database = click.prompt("Enter database name to connect, or enter new name to create a new falcon_multiqc database")
            if (database,) in databases:
                create_config(username, password, server_address, database) # re-create config file with proper connection URL 
                if server_address:
                    check_db_engine = create_engine(f'postgres+psycopg2://{username}:{password}@{server_address[0]}:{server_address[1]}/{(database,)[0]}')
                else:
                    check_db_engine = create_engine(f'postgres+psycopg2://{username}:{password}@localhost:5432/{(database,)[0]}')
                inspector = inspect(check_db_engine)
                if not falcon_multiqc_schema == inspector.get_table_names():
                    click.echo("\n===\nWarning, selected database is not a falcon_multiqc database, please try again or create a new database\n===\n")
                    continue
                check_db_engine.dispose()
            else:
                """Creates a new database"""
                click.echo("Creating new database...")
                create_config(username, password, server_address, database) 
                conn.execute("commit") # databases cannot be created inside transactions, this line will close the previous transaction 
                conn.execute(f"create database {database}") # create an empty database 
                from database.crud import create_database
                create_database() # populate the database with tables 
                click.echo("Database has been created!")
            break
        click.echo(f"You are now connected to database {database}!")
    login_engine.dispose()
