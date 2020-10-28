import click
import subprocess
import sys
import operator

from database.crud import session_scope
from database.models import Base, Sample, Batch, Cohort, RawData
from sqlalchemy import Float
from sqlalchemy.orm import load_only, Load, Query
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
falcon_multiqc query --tool_metric picard_wgsmetrics PCT_EXC_DUPE '<=' 0.5 --multiqc -d path

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

# Returns a sqlaclhemy query, selecting on the given columns.
# Columns supported: 'sample' (sample_name), 'batch', 'cohort', 'tool'.
# tool_metric is used to determine what metric to select on, if filtered.
def query_select(session, columns, tool_metric_filters, multiqc):
    # Add the Sqlalchemy class columns needed for the given column selection.
    select_cols = []

    # Order of the following columns will be the order of output columns.
    for col in columns:
        if col == 'sample':
            select_cols.extend([Sample.id, Sample.sample_name])
        if col == 'cohort':
            select_cols.append(Cohort.id)
        if col == 'batch':
            select_cols.append(Batch.batch_name)
        if col == 'tool-metric':
            select_cols.append(RawData.qc_tool)
            # If filtering on tool, we need to select for the tool metrics.
            if tool_metric_filters:
                for tm in tool_metric_filters:
                    # Use the metric name as this column's alias.
                    c = RawData.metrics[tm[1]].label(tm[1])
                    c.quote = True
                    select_cols.append(c)
    if multiqc:
        # Need to add batch paths.
        select_cols.append(Batch.path)

    query = Query(select_cols, session=session)

    # Add the table joins needed for the given column selection.
    if 'sample' in columns or 'batch' in columns:
        # We need Batch for batch.path for both sample and batch.
        query = query.join(Batch, Sample.batch_id == Batch.id)
    
    if 'tool-metric' in columns: 
        query = query.join(RawData, Sample.id == RawData.sample_id)

    if 'cohort' in columns:
        query = query.join(Cohort, Sample.cohort_id == Cohort.id)

    return query

# TODO: Currently only supports metrics that are float values. Support more.
# Returns a sqlalchemy query that queries the database with a filter
# created from the given tool, attribute, operator and value. 
def query_metric(session, query, tool, attribute, operator, value):
    if operator not in ops:
        # If user has not given a valid operator, do not filter on metric, just tool.
        return query.filter(RawData.qc_tool == tool)
    return query.filter(RawData.qc_tool == tool, ops[operator](RawData.metrics[attribute].astext.cast(Float), value))

@click.command()
@click.option('--select', multiple=True, default=["sample"], type=click.Choice(["sample", "batch", "cohort", "tool-metric"], case_sensitive=False), required=False, help="What to select on (sample_name, batch, cohort, tool), default is sample_name.")
@click.option('--tool_metric', multiple=True, type=(str, str, str, str), required=False, help="Filter by tool, metric, operator and number, e.g. 'verifybamid AVG_DP < 30'.")
@click.option('--batch', multiple=True, required=False, help="Filter by batch name: enter which batches e.g. AAA, BAA, etc.")
@click.option('--cohort', multiple=True, required=False, help="Filter by cohort id: enter which cohorts e.g. MGRB, cohort2, etc.")
@click.option('--multiqc', is_flag=True, required=False, help="Create a multiqc report (user must select only for sample_name if so).")
@click.option('--csv', is_flag=True, required=False, help="Create a csv report.")
@click.option("-o", "--output", type=click.Path(), required=True, help="Output directory where query result will be saved.")
def cli(select, tool_metric, batch, cohort, multiqc, csv, output):
    """Query the falcon qc database by specifying what you would like to select on by using the --select option, and
    what to filter on (--tool_metric, --batch, or --cohort)."""

    if multiqc and "sample" not in select:
        click.echo(
            "When multiqc report is selected, please ensure to select for sample.")
        sys.exit(1)

    click.echo(f"Returning {select} by filtering for:")
    [click.echo(f'{tm}') for tm in tool_metric]
    [click.echo(f'{b}') for b in batch]
    [click.echo(f'{c}') for c in cohort]

    # Keep track of the query header with query.column_descriptions. 
    # TODO: This should be updated if the query is altered.
    query_header = []
    # Sqlaclehmy query that will be constructed based on this command's options.
    falcon_query = None

    ### ================================= SELECT  ==========================================####
    with session_scope() as session:
        falcon_query = query_select(session, select, tool_metric, multiqc)

    ### ================================= FILTER  ==========================================####
    ## 1. Tool - Metric
    if tool_metric:
        with session_scope() as session:
            for query in tool_metric:
                falcon_query = query_metric(session, falcon_query, query[0], query[1], query[2], query[3])
    """
    ## 2. Cohort
    # TODO: implement filter by cohort: for potential future layout idea.

    if cohort:
        add cohort filter to falcon_query
    """
    """
    ## 3. Batch
    # TODO: implement filter by batch: for potential future layout idea.
    if batch:
        add batch filter to falcon_query
    """

    ### ============================== RESULT / OUTPUT =======================================####
    if falcon_query == None:
        raise Exception("No results from query")

    # Create header from the current query (falcon_query).
    for col in falcon_query.column_descriptions:
        query_header.append(col["entity"].__tablename__ + "." + col["name"])

    if multiqc:
        click.echo("Creating multiqc report...")
        create_new_multiqc([(row.sample_name, row.path) for row in falcon_query], output)

    if csv:
        click.echo("creating csv report...")
        create_csv(query_header, falcon_query, output)
