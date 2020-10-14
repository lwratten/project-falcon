import click
from database.crud import session_scope
from database.models import Base, Cohort

# Command for creating a new cohort inside the database.
@click.command()
def cli():
    """Creates a new Cohort inside the database and prints its primary key to stdout."""

    with session_scope() as session:
        # TODO: possibly get cohort information like disease or etc.
        cohort = Cohort()
        session.add(cohort)

        # Flush manually here to generate the cohort's primary key
        session.flush()

        # Cohort primary key is sent to stdout.
        click.echo(cohort.id)
