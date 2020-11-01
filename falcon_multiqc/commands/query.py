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
    - Add multiple selections by using multiple `--select` options)
    - The order of these --select/s are the column order of output.

Add optional filtering with --batch, --cohort, or --tool_metric.
    --batch <batch name> (behaves like OR when multiple)
    --cohort <cohort id> (behaves like OR when multiple)
    --tool-metric <tool name> <metric> <operator> <value> (behaves like AND when multiple)
    (Add multiple filters by using multiple `--batch` / `--cohort` / `--tool-metric' options)

Note (--tool_metric): 
    You must always specify 4 values. 

    If any <operator> is not valid, output will have the <metric>s - with no filtering. So,
    to simply output all samples with a metric, use <tool> <metric> 0 0.

    MUST be the first argument to falcon_multiqc query.

    Special characters must be escaped (wrapped in single quotes) in bash, like '<'.

See example equivalent SQL of what this command does at the end of this file.
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

    # Order of the column output is the order of user's --select input.
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
def query_metric(query, select, tool_metric):
    group_by_columns = []

    if 'sample' in select:
        group_by_columns.append(Sample.id)

    if 'batch' in select:
        group_by_columns.append(Batch.id)
    
    if 'cohort' in select:
        group_by_columns.append(Cohort.id)

    # Check operator validity.
    # If ANY operator is invalid - we detect user wants to filter based on metric (WITHOUT a conditional value).
    for tm in tool_metric:
        if tm[2] not in ops:
            return (query.filter(or_(RawData.qc_tool == tool for tool, attribute, operator, value in tool_metric))
                .group_by(*group_by_columns).having(func.count(RawData.qc_tool) == len(tool_metric)))

    return (query.filter(or_(and_(RawData.qc_tool == tool, ops[operator](RawData.metrics[attribute].astext.cast(Float), value)) 
                for tool, attribute, operator, value in tool_metric))
            .group_by(*group_by_columns).having(func.count(RawData.qc_tool) == len(tool_metric)))

@click.command()
@click.option(
    "-s",
    "--select",
    multiple=True,
    type=click.Choice(["sample", "batch", "cohort", "tool-metric"], case_sensitive=False),
    default=["sample"],
    required=False,
    help="What to select on (sample_name, batch, cohort, tool), default is sample_name.")

@click.option (
    "-tm",
    "--tool-metric", 
    multiple=True, 
    type=(str, str, str, str), 
    required=False, 
    help="Filter by tool, metric, operator and number, e.g. 'verifybamid AVG_DP < 30'.")

@click.option(
    "-b",
    "--batch",
    multiple=True,
    required=False,
    help="Filter by batch name: enter which batches e.g. AAA, BAA, etc.")

@click.option(
    "-c",
    "--cohort",
    multiple=True,
    required=False,
    help="Filter by cohort id: enter which cohorts e.g. MGRB, cohort2, etc.")

@click.option(
    "-bd",
    "--batch-description",
    multiple=True,
    required=False,
    help="Filter by batch description contents (contains).")

@click.option(
    "-cd",
    "--cohort-description",
    multiple=True,
    required=False,
    help="Filter by cohort description contents (contains).")

@click.option(
    "-sd",
    "--sample-description",
    multiple=True,
    required=False,
    help="Filter by sample description contents (contains).")

@click.option(
    "-fcl",
    "--flowcell-lane",
    multiple=True,
    required=False,
    help="Filter by sample flowcell lane.")

@click.option(
    "-li",
    "--library-id",
    multiple=True,
    required=False,
    help="Filter by sample library id.")

@click.option(
    "-pl",
    "--platform",
    multiple=True,
    required=False,
    help="Filter by sample platform.")

@click.option(
    "-ctr",
    "--centre",
    multiple=True,
    required=False,
    help="Filter by sample centre.")

@click.option(
    "-rf",
    "--reference",
    multiple=True,
    required=False,
    help="Filter by sample reference genome.")

@click.option(
    "-t",
    "--type",
    multiple=True,
    required=False,
    help="Filter by sample type.")

@click.option(
    "--multiqc",
    is_flag=True,
    required=False,
    help="Create a multiqc report (user must select only for sample_name if so).")

@click.option(
    "--csv", 
    is_flag=True, 
    required=False, 
    help="Create a csv report.")

@click.option(
    "-o",
    "--output",
    type=click.Path(),
    required=True,
    help="Output directory where query result will be saved.")    

def cli(
    select,
    tool_metric,
    batch,
    cohort,
    batch_description,
    cohort_description,
    sample_description,
    flowcell_lane,
    library_id,
    platform,
    centre,
    reference,
    type,
    multiqc,
    csv,
    output):

    """Query the falcon qc database by specifying what you would like to select on by using the --select option, and
    what to filter on (--tool_metric, --batch, or --cohort)."""

    if multiqc and "sample" not in select:
        click.echo(
            "When multiqc report is selected, please ensure to select for sample.")
        sys.exit(1)

    # Sqlaclehmy query that will be constructed based on this command's options.
    falcon_query = None

    ### ================================= SELECT  ==========================================####

    with session_scope() as session:
        falcon_query = query_select(session, select, tool_metric, multiqc)

    ### ================================= FILTER  ==========================================####

    ## 1. Sample
    if tool_metric:
        falcon_query = query_metric(falcon_query, select, tool_metric)

    if sample_description:
        conditions = [Sample.description.contains(d, autoescape=True) for d in sample_description]
        falcon_query = falcon_query.filter(or_(*conditions))
    
    if flowcell_lane:
        falcon_query = falcon_query.filter(Sample.flowcell_lane.in_(flowcell_lane))

    if library_id:
        falcon_query = falcon_query.filter(Sample.library_id.in_(library_id))
    
    if platform:
        falcon_query = falcon_query.filter(Sample.platform.in_(platform))

    if centre:
        falcon_query = falcon_query.filter(Sample.platform.in_(centre))

    if reference:
        falcon_query = falcon_query.filter(Sample.reference_genome.in_(reference))

    if type:
        falcon_query = falcon_query.filter(Sample.type.in_(type))

    ## 2. Cohort
    if cohort:
        falcon_query = falcon_query.filter(Cohort.id.in_(cohort))
        
    if cohort_description:
        conditions = [Cohort.description.contains(d, autoescape=True) for d in cohort_description]
        falcon_query = falcon_query.filter(or_(*conditions))

    ## 3. Batch
    if batch:
        falcon_query = falcon_query.filter(Batch.batch_name.in_(batch))

    if batch_description:
        conditions = [Batch.description.contains(d, autoescape=True) for d in batch_description]
        falcon_query = falcon_query.filter(or_(*conditions))

    ### ============================== RESULT / OUTPUT =======================================####
    if falcon_query == None:
        raise Exception("No results from query")

    # Create header from the current query (falcon_query).
    query_header = []
    for col in falcon_query.column_descriptions:
        query_header.append(col["entity"].__tablename__ + "." + col["name"])

    if multiqc:
        click.echo("Creating multiqc report...")
        create_new_multiqc([(row.sample_name, row.path) for row in falcon_query], output)

    if csv:
        click.echo("Creating csv report...")
        create_csv(query_header, falcon_query, output)

    if not multiqc and not csv:
        # Print result
        click.echo(query_header)
        for row in falcon_query:
            click.echo(row)

"""
Query: 
    falcon_multiqc query --select sample --select tool-metric \
    -tm verifybamid AVG_DP '<' 28 \
    -tm picard_insertSize MEAN_INSERT_SIZE '>' 490 \
    -o output

SQL:
    SELECT sample.id AS sample_id, 
    sample.sample_name AS sample_sample_name,
    max(raw_data.metrics ->> 'AVG_DP') AS AVG_DP, -- results in AVG_DP as its own column
    max(raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS MEAN_INSERT_SIZE -- results in MEAN_INSERT_SIZE as its own column
    FROM sample JOIN batch ON sample.batch_id = batch.id JOIN raw_data ON sample.id = raw_data.sample_id 

    WHERE (raw_data.qc_tool='verifybamid' AND CAST((raw_data.metrics ->> 'AVG_DP') AS FLOAT) < 28) 
    OR (raw_data.qc_tool='picard_insertSize' AND CAST((raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS FLOAT) > 490) 

    GROUP BY sample.id HAVING count(distinct raw_data.qc_tool) = 2 -- prevents duplicate sample.id rows
"""
