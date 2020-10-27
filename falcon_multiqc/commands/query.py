import click
import subprocess
import sys
import operator

from database.crud import session_scope
from database.models import *
from sqlalchemy import Float
from sqlalchemy.orm import load_only, Load
from database.process_query import create_new_multiqc, create_csv

"""
This command allows you to query the falcon multiqc database.

#TODO: add all argument required and optional and explanations here, similar to save.py.

Example commands (small):
falcon_multiqc query --tool_metric verifybamid AVG_DP '<' 28 --multiqc -d path
falcon_multiqc query --tool_metric picard_insertSize MEAN_INSERT_SIZE '>' 565 --multiqc -d path
falcon_multiqc query --tool_metric picard_wgsmetrics PCT_EXC_DUPE '<=' 0.04 --multiqc -d path

Example commands (large):
falcon_multiqc query --tool_metric verifybamid AVG_DP '<' 100 --multiqc -d path
falcon_multiqc query --tool_metric picard_insertSize MEAN_INSERT_SIZE '>' 390 --multiqc -d path
falcon_multiqc query --tool_metric picard_wgsmetrics PCT_EXC_DUPE '<=' 0.021 --multiqc -d path

Notes:
Special characters must be escaped (wrapped in single quotes) in bash, like '<'.
--tool_metric MUST be the first argument.
Multiple --tool_metric's can be added as input. 

"""

ops = {
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt,
    '<=': operator.le,
    '==': operator.eq,
    '!=': operator.ne
}

# TODO: Currently only supports metrics that are float values. Support more.


def query_metric(session, query, tool, attribute, operator, value):
    if not query:
        return (session.query(Sample.id, Sample.sample_name, Batch.path, Batch.batch_name, Cohort.id, RawData.qc_tool)
                .join(RawData, Sample.id == RawData.sample_id)
                .join(Batch, Sample.batch_id == Batch.id)
                .join(Cohort, Sample.cohort_id == Cohort.id)
                .filter(RawData.qc_tool == tool, ops[operator](RawData.metrics[attribute].astext.cast(Float), value)))
    else:
        return (query.union(session.query(Sample.id, Sample.sample_name, Batch.path, Batch.batch_name, Cohort.id, RawData.qc_tool)
                            .join(RawData, Sample.id == RawData.sample_id)
                            .join(Batch, Sample.batch_id == Batch.id).join(Cohort, Sample.cohort_id == Cohort.id)
                            .filter(RawData.qc_tool == tool, ops[operator](RawData.metrics[attribute].astext.cast(Float), value))))


@click.command()
@click.option('--tool_metric', multiple=True, type=(str, str, str, str), required=False, help="Filter by tool, metric, operator and number, e.g. 'verifybamid AVG_DP < 30'.")
@click.option('--select', multiple=True, default=["sample_name"], type=click.Choice(["sample_name", "batch", "cohort", "tool"], case_sensitive=False), required=False, help="What to select on (sample_name, batch, cohort, tool), default is sample_name.")
@click.option('--batch', multiple=True, required=False, help="Filter by batch name: enter which batches e.g. AAA, BAA, etc.")
@click.option('--cohort', multiple=True, required=False, help="Filter by cohort id: enter which cohorts e.g. MGRB, cohort2, etc.")
@click.option('--multiqc', is_flag=True, required=False, help="Create a multiqc report (user must select only for sample_name if so).")
@click.option('--csv', is_flag=True, required=False, help="Create a csv report.")
@click.option("-o", "--output", type=click.Path(), required=True, help="Output directory where query result will be saved.")
def cli(select, tool_metric, batch, cohort, multiqc, csv, output):
    """Query the falcon qc database by specifying what you would like to select on by using the --select option, and
    to filter on either --tool_metric, --batch, or --cohort."""

    if multiqc and "sample_name" not in select:
        click.echo(
            "When multiqc report is selected, please ensure to select for sample_name.")
        sys.exit(1)

    click.echo(f"Returning {select} by filtering for:")
    [click.echo(f'{tm}') for tm in tool_metric]
    [click.echo(f'{b}') for b in batch]
    [click.echo(f'{c}') for c in cohort]

    ### ================================= FILTER SECTION ==========================================####

    # Having a global set which contains all these means you can perform any potential SELECT action (see the SELECT SECTION)
    sample_query_set = set()
    # Keep track of the query header with query.column_descriptions. 
    # TODO: This should be updated if the query is altered.
    query_header = []

    if tool_metric:
        with session_scope() as session:
            tm_query = None
            for query in tool_metric:
                tool = query[0]
                attribute = query[1]
                operator = query[2]
                value = query[3]

                tm_query = query_metric(
                    session, tm_query, tool, attribute, operator, value)

            # creates set containing every RawData.sample_id filtered accross database which satifies filtering, this acts as a global query set for samples
            sample_query_set = set(tm_query.all())

            for col in tm_query.column_descriptions:
                query_header.append(col["name"])

    # TODO: implement filter by cohort: for potential future layout idea.
    """
    if cohort:
        with session_scope() as session:
            for query in cohort:
                # c_query = session.query(Sample.sample_name, Batch.path, Batch.batch_name, Cohort.id).join(RawData, Sample.id == RawData.sample_id).join(Batch, Sample.batch_id == Batch.id).join(Cohort, Sample.cohort_id == Cohort.id). ETC
                pass
            if sample_query_set:
                sample_query_set = sample_query_set.intersection(
                    sample_query_set, set(c_query.all()))
            else:
                sample_query_set = set(c_query.all())
    """
    """
    # TODO: implement filter by batch: for potential future layout idea.
    if batch:
        with session_scope() as session:
            for query in batch:
                # b_query = session.query(Sample.sample_name, Batch.path, Batch.batch_name, Cohort.id).join(RawData, Sample.id == RawData.sample_id).join(Batch, Sample.batch_id == Batch.id).join(Cohort, Sample.cohort_id == Cohort.id). ETC
                pass
            if sample_query_set:  # if the global sample query set is NOT empty, then get intersection with the batch sample query result
                sample_query_set = sample_query_set.intersection(
                    sample_query_set, set(b_query.all()))
            else:
                # if the global sample query set IS empty, then populate it with the batch query result etc.
                sample_query_set = set(b_query.all())
    """

    ### ================================= SELECT SECTION ==========================================####

    # if select contains sample_name, list of sample_name/path will be made from the query
    if 'sample_name' in select:
        with session_scope() as session:
            sample_path_list = []
            click.echo(f'total query was: {len(sample_query_set)}')
            # used by multiqc function
            sample_path_list = [(query[1], query[2])
                                for query in sample_query_set]

    # example
    if 'qctool' in select:
        with session_scope() as session:
            tool_list = []
            for row in sample_query_set:  # set contains rows consisting of: sample.id, sample_name, batch path, batch_name, cohort.id and tool, so choose what to use
                tool = session.query(RawData.qc_tool).filter(
                    Sample.id == row[0]).first()
                tool_list.append(tool)  # list of tuples
            tool_set = set(tool_list)

    # example
    if 'metric' in select:
        with session_scope() as session:
            metric_list = []
            for row in sample_query_set:  # set contains rows consisting of: sample.id, sample_name, batch path, batch_name, cohort.id and tool, so choose what to use
                metric = session.query(RawData.metrics).filter(
                    Sample.id == row[0]).first()
                metric_list.append(metric)  # list of tuples
            metric_set = set(metric_list)

    # example
    if 'batch' in select:
        with session_scope() as session:
            batch_list = []
            for row in sample_query_set:  # set contains rows consisting of: sample.id, sample_name, batch path, batch_name, cohort.id and tool, so choose what to use
                batch_name = session.query(Batch.batch_name).filter(
                    Sample.id == row[0]).first()
                batch_list.append(batch_name)  # list of tuples
            batch_set = set(batch_list)

    # example
    if 'sample_batch' in select:
        with session_scope() as session:
            sample_batch_list = []
            for row in sample_query_set:  # set contains rows consisting of: sample.id, sample_name, batch path, batch_name, cohort.id and tool, so choose what to use
                sample_name, batch_name = session.query(Sample.sample_name, Batch.batch_name).join(
                    Batch).filter(Sample.id == row[0]).first()
                sample_batch_list.append(
                    (sample_name, batch_name))  # list of tuples
            sample_batch_set = set(sample_batch_list)

    if multiqc:
        click.echo("creating multiqc report...")
        create_new_multiqc(sample_path_list, output)

    if csv:
        # TODO: Change tm_query input if the input changes from the above selecting.
        click.echo("creating csv report...")
        create_csv(query_header, tm_query, output)
