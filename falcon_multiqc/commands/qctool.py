import click
import subprocess
from database.crud import session_scope
from database.models import *
from sqlalchemy import Float
from sqlalchemy.orm import load_only,Load

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


        #create a list to store the path
        paths = []
        for x in sample_list:
            #print(x.sample_id)
            path = session.query(Batch.path).join(Sample).\
                filter(
                Sample.id == x.sample_id).\
                options(Load(Batch).load_only('path')).first()

            paths.append(path)

    #save results into file
    click.echo("saving file sample's path in current directory...")
    file = f'{tool}{n}{v} data for multiqc.txt'
    with open(file,'w') as f:
        for item in paths:
            f.write("%s\n" % item[0])
    click.echo("files saved!")

