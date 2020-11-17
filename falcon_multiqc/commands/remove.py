import click
from database.crud import session_scope
from sqlalchemy.orm import Query
from .query import print_overview
from database.models import Base, Batch, Cohort

"""
Command for removing entries from database.

--overview Prints an overview of the number of samples in each batch/cohort.

--cohort <cohortID> - removes all entries associated with that cohort throughout database, can be used multiple times.

--batch <cohortID Batch_name> - removes all entries associated with that batch throughout database, can be used multiple times.

NOTE: Don't use --batch or --cohort options in one command, use two seperate commands instead.

"""

@click.option("-c", "--cohort", multiple=True, required=False, help="Which cohort to remove from the database. E.g. <MGRB>")
@click.option ("-b", "--batch", multiple=True, type=(str, str), required=False, help="Which batch you want to remove from the database. E.g. <MGRB BAB>")
@click.option("--overview", is_flag=True, required=False, help="Prints an overview of the number of samples in each batch/cohort.")
@click.command()
def cli(cohort, batch, overview):
    """Removes all associated rows of specified batch/cohort from database."""

    with session_scope() as session:
        if cohort:
            for cohort_id in cohort:
                if session.query(Cohort.id).filter(Cohort.id == cohort_id).scalar() is None:  
                    # Roll back of all changes made during this session.          
                    raise Exception(f"No cohort {cohort_id} is present in the database. Nothing has been deleted."
                                    "\nRun --overview option to see what is currently present.")
                else:
                    # Delete all assoicated rows
                    session.query(Cohort.id).filter(Cohort.id == cohort_id).delete()
                    if batch:
                        raise Exception("\nBoth --cohort and --batch used in the same command, please try again as two seperate commands."
                        f"\nNothing has been deleted from the database.")
            click.echo(f"Cohort(s) {list(cohort)} and all assoicated entries have been deleted.")
        elif batch:
            for cohort_id, batch_name in batch:
                if session.query(Batch.id).filter(Batch.batch_name == batch_name,Batch.cohort_id == cohort_id).scalar() is None:
                    # Roll back of all changes made during this session.          
                    raise Exception(f"No batch {batch_name} is present in the database. Nothing has been deleted."
                                    "\nRun --overview option to see what is currently present.")
                else:
                    # Delete all assoicated rows
                    session.query(Batch.id).filter(Batch.batch_name == batch_name,Batch.cohort_id == cohort_id).delete()
            click.echo(f"Batch(s) {list(batch)} and all assoicated entries have been deleted.")
    if overview:
        print_overview(session)
