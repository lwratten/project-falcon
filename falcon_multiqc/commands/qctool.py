import click
import subprocess
from database.crud import session_scope
from database.models import *
from sqlalchemy import Float
from sqlalchemy.orm import load_only,Load

#falcon_multiqc query --tool verifybamid --n AVG_DP --v 30
#will return you a sample list using qctool verifybamid which ACG_DP is smaller than 30
@click.command()
@click.option("--tool", prompt="qctool name (eg: verifybamid)", help="qc tool you want to query")#CollectWgsMetric
@click.option("--m", prompt="metric filtering(PLEASE use '#' between words) (eg: AVG_DP#30#-) ", help="please type attributes, operator(smaller(-), larger(+), not smaller(+=), not larger(-=), equal(=), not equal(!=)), value in json file") #MEAN_COVERAGE
#@click.option("--v", type = float, prompt="value to filter", help="Provide largest number") #30
#@click.option("--n", prompt="json column", help="attributes in json file") #MEAN_COVERAGE


def cli(tool,m):
    attribute = m.split('#')[0]
    value = float(m.split('#')[1])
    operator = m.split('#')[2]
    print(attribute,operator,value)




    with session_scope() as session:
        if operator == '-':
            sample_list = session.query(RawData). \
                filter(
                RawData.qc_tool == tool). \
                filter(
                RawData.metrics[attribute].astext.cast(Float) < value).all()
            session.expire_on_commit = False
        # print(sample_list)
        if operator == '+':
            sample_list = session.query(RawData). \
                filter(
                RawData.qc_tool == tool). \
                filter(
                RawData.metrics[attribute].astext.cast(Float) > value).all()
            session.expire_on_commit = False
        if operator == '=':
            sample_list = session.query(RawData). \
                filter(
                RawData.qc_tool == tool). \
                filter(
                RawData.metrics[attribute].astext.cast(Float) == value).all()
            session.expire_on_commit = False
        if operator == '+=':
            sample_list = session.query(RawData). \
                filter(
                RawData.qc_tool == tool). \
                filter(
                RawData.metrics[attribute].astext.cast(Float) >= value).all()
            session.expire_on_commit = False
        if operator == '-=':
            sample_list = session.query(RawData). \
                filter(
                RawData.qc_tool == tool). \
                filter(
                RawData.metrics[attribute].astext.cast(Float) <= value).all()
            session.expire_on_commit = False
        if operator == '!=':
            sample_list = session.query(RawData). \
                filter(
                RawData.qc_tool == tool). \
                filter(
                RawData.metrics[attribute].astext.cast(Float) != value).all()
            session.expire_on_commit = False






        sample_list = session.query(RawData). \
            filter(
            RawData.qc_tool == tool).\
            filter(
            RawData.metrics[attribute].astext.cast(Float) <= value ).all()
        session.expire_on_commit = False
    #print(sample_list)


#create a list to store the path
    paths = []
    for x in sample_list:
        #print(x.sample_id)
        path = session.query(Batch.path).join(Sample).\
            filter(
            Sample.id == x.sample_id).\
            options(Load(Batch).load_only('path')).first()

        paths.append(path)
        print(path)

    #save results into file
    click.echo("saving file sample's path in current directory...")
    file = f'{tool}{attribute}{value}{operator} data for multiqc.txt'
    with open(file,'w') as f:
        for item in paths:
            f.write("%s\n" % item[0])
    click.echo("files saved!")



