import click
import subprocess
import sys
import operator

from database.crud import session_scope
from database.models import Base, Sample, Batch, Cohort, RawData
from sqlalchemy import Float, or_, and_, func
from sqlalchemy.orm import load_only, Load, Query
from database.process_query import create_new_multiqc, create_csv

"""
This command allows you to query the falcon multiqc database.

Select columns to include in output (sample [default], batch, cohort, tool-metric).
    --select <sample>
    (Add multiple selections by using multiple `--select` options)

Add optional filtering with --batch, --cohort, or --tool_metric.
    --batch <batch name>
    --cohort <cohort id>
    --tool-metric <tool name> <metric> <operator> <value>
    (Add multiple filters by using multiple `--batch` / `--cohort` / `--tool-metric' options)

Note (--tool_metric): 
    You must always specify 4 values. If <operator> is not valid,
    this is okay and the output will have the <metric> - with no filtering.

    MUST be the first argument to falcon_multiqc query.

    Special characters must be escaped (wrapped in single quotes) in bash, like '<'.
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
            # If filtering on tool, we need to select for the tool metrics.
            if tool_metric_filters:
                for tm in tool_metric_filters:
                    # Use the metric name as this column's alias.
                    c = func.max(RawData.metrics[tm[1]].astext).label(tm[1])
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
# with the given tool, attribute, operator and value.
def query_metric(session, query, operators, tool_metric):
    for opr in operators:
        # If user has not given a valid operator, do not filter on metric, just tool.
        if opr not in ops:
            # NOTE this doesn't really work as intended, because if only 1/4 opr are not in ops it will still query all tools - need better method
            return query.filter(or_(RawData.qc_tool == tool for tool, attribute, operator, value in tool_metric))

    return (query.filter(or_(and_(RawData.qc_tool == tool, ops[operator](RawData.metrics[attribute].astext.cast(Float), value)) 
                for tool, attribute, operator, value in tool_metric))
            .group_by(Sample.id, Batch.id).having(func.count(RawData.qc_tool) == len(tool_metric)))

@click.command()
@click.option("-s", "--select", multiple=True, default=["sample"], type=click.Choice(["sample", "batch", "cohort", "tool-metric"], case_sensitive=False), required=False, help="What to select on (sample_name, batch, cohort, tool), default is sample_name.")
@click.option("-tm", "--tool-metric", multiple=True, type=(str, str, str, str), required=False, help="Filter by tool, metric, operator and number, e.g. 'verifybamid AVG_DP < 30'.")
@click.option("-b", "--batch", multiple=True, required=False, help="Filter by batch name: enter which batches e.g. AAA, BAA, etc.")
@click.option("-c", "--cohort", multiple=True, required=False, help="Filter by cohort id: enter which cohorts e.g. MGRB, cohort2, etc.")
@click.option("--multiqc", is_flag=True, required=False, help="Create a multiqc report (user must select only for sample_name if so).")
@click.option("--csv", is_flag=True, required=False, help="Create a csv report.")
@click.option("-o", "--output", type=click.Path(), required=True, help="Output directory where query result will be saved.")
def cli(select, tool_metric, batch, cohort, multiqc, csv, output):
    """Query the falcon qc database by specifying what you would like to select on by using the --select option, and
    what to filter on (--tool_metric, --batch, or --cohort)."""

    if multiqc and "sample" not in select:
        click.echo(
            "When multiqc report is selected, please ensure to select for sample.")
        sys.exit(1)

    # Keep track of the query header with query.column_descriptions. 
    # TODO: This should be updated if the query is altered.
    query_header = []
    # Sqlaclehmy query that will be constructed based on this command's options.
    falcon_query = None

    ### ================================= SELECT  ==========================================####

    with session_scope() as session:
        falcon_query = query_select(session, select, tool_metric, multiqc)

    ### ================================= FILTER  ==========================================####

    if tool_metric:
        operators = [o for t, m, o , v in tool_metric] # NOTE this is used to detecting false operators later on, don't really like it
        falcon_query = query_metric(session, falcon_query, operators, tool_metric) # inner query which returns sample_id which satisfy all tm filters simultanesouly

    ## 2. Cohort
    if cohort:
        falcon_query = falcon_query.filter(Cohort.id.in_(cohort))

    ## 3. Batch
    if batch:
        falcon_query = falcon_query.filter(Batch.batch_name.in_(batch))

    ### ============================== RESULT / OUTPUT =======================================####
    print(falcon_query)
    if falcon_query == None:
        raise Exception("No results from query")

    # Create header from the current query (falcon_query).
    for col in falcon_query.column_descriptions:
        print(col)
        query_header.append(col["entity"].__tablename__ + "." + col["name"])

    if multiqc:
        size = len(falcon_query.all())
        click.echo(f"Query returned {size} samples")
        if size == 0:
            click.echo("warning cannot create multiqc report with no query result, exiting")
            sys.exit(1)
        click.echo("Creating multiqc report...")
        create_new_multiqc([(row.sample_name, row.path) for row in falcon_query], output)

    if csv:
        click.echo("creating csv report...")
        create_csv(query_header, falcon_query, output)

    if not multiqc and not csv:
        # Print result
        click.echo(query_header)
        for row in falcon_query:
            click.echo(row)
