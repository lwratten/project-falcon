import click
import subprocess 
from database.crud import session_scope
from database.models import Base, Batch

# Command for viewing all avaliable batches, and allowing user to select and open multiqc.html file of selected batch 

@click.command()
def cli():
    """Lists all entries in Batch table, prompt asks user to select and open chosen batch multiqc.html file"""

    with session_scope() as session:
        click.echo("Current list of batches in database are:\n")
        batch_list = session.query(Batch.id, Batch.cohort_id, Batch.batch_name, Batch.description).all()
        [click.echo(f"Batch_ID {b[0]}:      Details (cohortID {b[1]}, batch name {b[2]}, description {b[3]})") for b in batch_list] 
        query = click.prompt("\nPlease enter the batch ID of the html you would like to open")

        try:
            html_path = session.query(Batch).filter(Batch.id == query).first().path + '/multiqc_report.html'
            click.echo(f'Opening batch ID {query}')
            subprocess.call(['xdg-open', html_path]) # in windows use os module, os.startfile(r'html_path')
        except AttributeError:
            click.echo("===\nBatch ID entered is not present in Batch table.\n===")
