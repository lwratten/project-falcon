import click
import subprocess 
from database.crud import session_scope
from database.models import Base, Batch

# Command for viewing all avaliable batches, and allowing user to select and open multiqc.html file of selected batch 

@click.command()
def cli():
    """Lists all entries in Batch table, prompt asks user to select and open chosen batch multiqc.html file"""

    with session_scope() as session:
        # TODO: possibly get cohort information like disease or etc.
        click.echo("Current list of batches in database are:\n")
        batch_list = session.query(*[c for c in Batch.__table__.c if c.name != 'path']).all()
        [click.echo(f"Batch_ID {b[0]}:      Details (cohortID {b[1]}, flowCell {b[2]}, date {b[3]})") for b in batch_list] 
        query = click.prompt("\nPlease enter the batch ID of the html you would like to open")
        # html_path = session.query(Batch.__table__.c.name == path)
        try:
            html_path = session.query(Batch).filter(Batch.id == query).first().path + '/multiqc_report.html'
            click.echo(f'Opening batch ID {query}')
            subprocess.call(['xdg-open', '/' + html_path]) # in windows use os module, os.startfile(r'html_path')
        except AttributeError:
            click.echo("===\nBatch ID entered is not present in Batch table.\n===")

