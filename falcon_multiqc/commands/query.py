import click
import subprocess
import sys
from database.crud import session_scope
from database.models import *
from sqlalchemy import Float
from sqlalchemy.orm import load_only,Load
from database.process_query import create_new_multiqc

# example command:
# falcon_multiqc query --tool_metric --multiqc -d path
# User will get prompted due to -tm flag, command will ask for which tool_metrics to filter on
# examples
# verifybamid AVG_DP < 28
# picard_insertSize MEAN_INSERT_SIZE > 565
# picard_wgsmetrics PCT_EXC_DUPE <= 0.04
# Then hit 'enter'

@click.command()
@click.option('--select', is_flag=True, required=False, help = "Enter what you want to select on, e.g. select for sample_name, batch, etc. (deafult is sample_name)")
@click.option('--tool_metric', is_flag=True, required=False, help = "Enter tool, metric, operator and number, e.g. verifybamid AVG_DP < 30")
@click.option('--batch', is_flag=True, required=False, help = "Enter which batches to filter on e.g. AAA, BAA, etc.")
@click.option('--cohort', is_flag=True, required=False, help = "Enter which cohort to filter on e.g. MGRB, cohort2, etc.")
@click.option('--multiqc', is_flag=True, required=False, help = "Creates a multiqc report (user must select only for sample_name if so)")
@click.option('--csv', is_flag=True, required=False, help = "Creates a csv report")
@click.option("-d", "--directory", type=click.STRING, required=True, help="where query result will be saved")
def cli(select, tool_metric, batch, cohort, multiqc, csv, directory):

    if not select:
        select = ['sample_name']
    else:
        click.echo("Enter what you want to select on from the database:\nOptions are: sample_name, batch, cohort, tool\nenter 'next' to finish")
        select = []
        while True:
            query = click.prompt("Select")
            if query == 'next':
                break
            select.append(query)

    if multiqc:
        if len(select) != 1 and select[0] != 'sample_name':
            click.echo("If multiqc report is selected, please ensure to select for only sample_name")
            sys.exit(1)

    tm_query_list = []
    if tool_metric:
        click.echo("Enter any number of queries in the form: <tool metric operator number>\nTo exit, enter nothing\n")
        while True:
            query = input("Query (tool/metric/operator/number): ") # note click.prompt is able to capture the 'enter' key, hence using input()
            if query == '':
                break
            if len(query.split()) != 4:
                click.echo('Incorrect format: Please enter 4 arguments <tool metric operator number> correctly')
                continue
            tm_query_list.append(query)
        

    # for potential future layout idea
    b_query_list = []
    if batch:
        # code
        pass

    # for potential future layout idea
    c_query_list = []
    if cohort:
        #code
        pass
    

    click.echo(f"Returning {select} by filtering for:")
    [click.echo(f'{tm}') for tm in tm_query_list]
    [click.echo(f'{b}') for b in b_query_list]
    [click.echo(f'{c}') for c in c_query_list]

    # start session 
    if tm_query_list:
        with session_scope() as session:
            first_loop = True
            for query in tm_query_list:
                query = query.split()
                tool = query[0]
                attribute = query[1]
                operator = query[2]
                value = query[3] 
                if operator == '<':
                    if first_loop:
                        tm_query = session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) < value)
                    else:
                        tm_query = tm_query.union(session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) < value))
                    session.expire_on_commit = False
                if operator == '>':
                    if first_loop:
                        tm_query = session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) > value)
                    else:
                        tm_query = tm_query.union(session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) > value))
                    session.expire_on_commit = False
                if operator == '==':
                    if first_loop:
                        tm_query = session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) == value)
                    else:
                        tm_query = tm_query.union(session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) == value))
                    session.expire_on_commit = False
                if operator == '>=':
                    if first_loop:
                        tm_query = session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) >= value)
                    else:
                        tm_query = tm_query.union(session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) >= value))
                    session.expire_on_commit = False
                if operator == '<=':
                    if first_loop:
                        tm_query = session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) <= value)
                    else:
                        tm_query = tm_query.union(session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) <= value))
                    session.expire_on_commit = False
                if operator == '!=':
                    if first_loop:
                        tm_query = session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) != value)
                    else:
                        tm_query = tm_query.union(session.query(RawData.sample_id).filter(RawData.qc_tool == tool, RawData.metrics[attribute].astext.cast(Float) != value))
                    session.expire_on_commit = False
                first_loop = False
            sample_query_set = set(tm_query.all()) # creates set containing every RawData.sample_id filtered accross database which satifies filtering, this acts as a global query set for samples

    # for potential future layout idea
    if b_query_list:
        with session_scope() as session: 
            first_loop = True
            b_query = None
            for query in b_query:
                pass
            if sample_query_set: # if the global sample query set is NOT empty, then get intersection with the batch sample query result 
                sample_query_set = sample_query_set.intersection(sample_query_set, set(b_query.all()))
            else:
                sample_query_set = set(b_query.all()) # if the global sample query set IS empty, then populate it with the batch query result etc. 

    # for potential future layout idea
    if c_query_list:
        with session_scope() as session:
            first_loop = True
            c_query = None
            for query in c_query:
                pass
            if sample_query_set:
                sample_query_set = sample_query_set.intersection(sample_query_set, set(c_query.all()))
            else:
                sample_query_set = set(c_query.all())

    # if select contains sample_name, list of sample_name/path will be made from the query
    if 'sample_name' in select:
        with session_scope() as session:
            sample_path_list = []
            click.echo(f'total query was: {len(sample_query_set)}') # temp
            for sample_id in sample_query_set: # this set will contain only sample_IDs which satisfy all fliter conditions (i.e. tool/metric/batch/cohort)
                sample_name, path = session.query(Sample.sample_name, Batch.path).join(Batch).filter(Sample.id == sample_id[0]).first()
                sample_path_list.append((sample_name, path)) # list of tuples

    if multiqc:
        click.echo("creating multiqc report...")
        create_new_multiqc(sample_path_list, directory)
