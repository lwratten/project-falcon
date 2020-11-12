import click
from database.crud import session_scope
from sqlalchemy.orm import Query
from sqlalchemy import update
from database.models import Base, Batch
from os.path import exists, basename, abspath

"""
Command for checking paths saved in the database are still valid.
--skip-update to stop the program from prompting the user for a valid path in the case of an invalid db bath.
"""

def check_db_paths(skip_update):
    with session_scope() as session:
        # Query the paths in the batch table
        paths = session.query(Batch.path)

        # We don't want to re-check the same path
        checked = []
        print("Checking database paths...")
        for path_tuple in paths:
            old_path = path_tuple[0]
            if old_path not in checked:
                # check it exists
                if exists(old_path):
                    # add it to checked
                    checked.append(old_path)
                else:
                    print(f"File '{basename(old_path)}' no longer exists at path '{old_path}'")
                    if not skip_update:
                        # Prompt for update
                        if click.confirm('Would you like to update this path now?'):
                            new_path = click.prompt(f"Please enter the correct path for the directory '{basename(old_path)}'")
                            # check the new path actually exists
                            new_path = abspath(new_path)
                            if exists(new_path):
                                print(f"Updating old path '{old_path}' to new path '{new_path}'")

                                session.query(Batch).filter(Batch.path == old_path).\
                                update({Batch.path: new_path}, synchronize_session = False)
                                
                                checked.append(old_path)
                            else:
                                print(f"Aborting update... file path '{new_path}' does not exist")
        print("Database check complete!")

@click.option("-s", "--skip-update",is_flag=True, required=False, help="Skip update prompts for invalid paths while checking the database.")
@click.command()
def cli(skip_update):
    """Checks the paths in the database are still valid and prompts for an update."""

    check_db_paths(skip_update)
        