import click
import subprocess
from database.crud import session_scope
from database.models import *
from sqlalchemy import Float

#falcon_multiqc query --tool verifybamid --n AVG_DP --v 30
#will return you a sample list using qctool verifybamid which ACG_DP is smaller than 30
@click.command()
@click.option("--tool", prompt="Your name", help="qc tool you want to query")#CollectWgsMetric
@click.option("--n", prompt="json column", help="attributes in json file") #MEAN_COVERAGE
@click.option("--v", type = float, prompt="value to filter", help="Provide largest number") #30
def cli(n,v,tool):
    with session_scope() as session:
        sample_list = session.query(RawData).\
            filter(
            RawData.metrics[n].astext.cast(Float) <= v ).all()

        for sample in sample_list:
            print(sample.id)


if __name__ == '__main__':
    cli()