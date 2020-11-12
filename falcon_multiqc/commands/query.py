import click
import subprocess
import sys
import operator
import os.path

from database.crud import session_scope
from database.models import Base, Sample, Batch, Cohort, RawData
from sqlalchemy import Float, or_, and_, func, distinct
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
def query_select(session, columns, join, tool_metric_filters, multiqc):
    # Add the Sqlalchemy class columns needed for the given column selection.
    select_cols = []

    # Order of the column output is the order of user's --select input.
    for col in columns:
        if col == 'sample':
            select_cols.extend([Sample.id, Sample.sample_name, Sample.flowcell_lane, Sample.library_id, Sample.platform, Sample.centre, Sample.reference_genome, Sample.description])
        if col == 'cohort':
            select_cols.extend([Cohort.id, Cohort.description])
        if col == 'batch':
            select_cols.extend([Batch.batch_name, Batch.description])
        if col == 'tool-metric':
            # If filtering on tool, we need to select for the tool metrics.
            if tool_metric_filters:
                for tm in tool_metric_filters:
                    # Use the metric name as this column's alias.
                    c = func.max(RawData.metrics[tm[1]].astext).label(tm[1])
                    c.quote = True
                    select_cols.append(c)
            else:
                select_cols.append(RawData.qc_tool)
    if multiqc:
        # Need to add batch paths.
        select_cols.append(Batch.path)

    query = Query(select_cols, session=session)
    join['joined'].add(columns[0]) # The first item in select query doesn't need to be explicitly joined

    ### ================================= JOIN  ==========================================####
    # Add the table joins needed for the given column selection or filtering.   

    if 'sample' in join['joins'] and 'sample' not in join['joined']:
        if 'tool-metric' in join['joined']:
            query = query.join(Sample, Sample.id == RawData.sample_id)
        elif 'batch' in join['joined']:
            query = query.join(Sample, Sample.batch_id == Batch.id)
        elif 'cohort' in join['joined']:
            query = query.join(Sample, Sample.cohort_id == Cohort.id)
        join['joined'].add('sample')

    # For multiqc we need Batch for batch.path.
    if (multiqc or 'batch' in join['joins']) and 'batch' not in join['joined']:
        if 'tool-metric' in join['joined'] and 'sample' not in join['joined']:
            query = query.join(Sample, Sample.id == RawData.sample_id)
            join['joined'].add('sample')
        if 'sample' in join['joined']:
            query = query.join(Batch, Batch.id == Sample.batch_id)
        elif 'cohort' in join['joined']:
            query = query.join(Batch, Batch.cohort_id == Cohort.id)
        join['joined'].add('batch')

    if 'cohort' in join['joins'] and 'cohort' not in join['joined']:
        if 'tool-metric' in join['joined'] and 'sample' not in join['joined']:
            query = query.join(Sample, Sample.id == RawData.sample_id)
            join['joined'].add('sample')
        if 'sample' in join['joined']:
            query = query.join(Cohort, Cohort.id == Sample.cohort_id)
        elif 'batch' in join['joined']:
            query = query.join(Cohort, Cohort.id == Batch.cohort_id)
        join['joined'].add('cohort')

    if 'tool-metric' in join['joins'] and 'tool-metric' not in join['joined']:
        if 'batch' in join['joined'] and 'sample' not in join['joined']:
            query = query.join(Sample, Sample.batch_id == Batch.id)
        elif 'cohort' in join['joined'] and 'sample' not in join['joined']:
            query = query.join(Sample, Sample.cohort_id == Cohort.id)
        query = query.join(RawData, RawData.sample_id == Sample.id)
        join['joined'].add('tool-metric')

    return query

# TODO: Currently only supports metrics that are float values. Support more.
# Returns a sqlalchemy query that queries the database with a filter
# with the given tool, attribute, operator and value.
def query_metric(query, join, tool_metric):
    group_by_columns = []
    
    if 'batch' in join['joined']:
        group_by_columns.append(Batch.id)
    
    if 'cohort' in join['joined']:
        group_by_columns.append(Cohort.id)

    if 'sample' in join['joined']:
        group_by_columns.append(Sample.id)
    
    if 'tool-metric' in join['joined']:
        group_by_columns.append(RawData.sample_id)

    # Check operator validity.
    # If ANY operator is invalid - we detect user wants to filter based on metric (WITHOUT a conditional value).
    for tm in tool_metric:
        if tm[2] not in ops:
            return (query.filter(or_(RawData.qc_tool == tool for tool, attribute, operator, value in tool_metric))
            .group_by(*group_by_columns).having(func.count(RawData.qc_tool) == len(tool_metric)))

    return (query.filter(or_(and_(RawData.qc_tool == tool, ops[operator](RawData.metrics[attribute].astext.cast(Float), value)) 
            for tool, attribute, operator, value in tool_metric)).group_by(*group_by_columns).
            having(func.count(distinct(RawData.qc_tool)) == len(tool_metric)))

def print_overview(session):
    for cohort_id, batch_name in session.query(Batch.cohort_id, Batch.batch_name):
        num_samples = session.query(Sample).join(Batch, Batch.id == Sample.batch_id).\
        filter(Batch.batch_name == batch_name, Sample.cohort_id == cohort_id).count()
        click.echo(f"Cohort '{cohort_id}' batch '{batch_name}' has {num_samples} number of samples")

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
    help="Create a multiqc report.")

@click.option(
    "--csv", 
    is_flag=True, 
    required=False, 
    help="Create a csv report.")

@click.option(
    "--overview", 
    is_flag=True, 
    required=False, 
    help="Prints an overview of the number of samples in each batch/cohort.")

@click.option(
    "-o",
    "--output",
    type=click.Path(),
    required=False,
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
    overview,
    output):

    """Query the falcon qc database by specifying what you would like to select on by using the --select option, and
    what to filter on (--tool_metric, --batch, or --cohort)."""

    if (multiqc or csv) and not output:
        click.echo("When using multiqc or csv option, please specify a directory to save in using the -o option")
        sys.exit(1)

    # Sqlaclehmy query that will be constructed based on this command's options.
    falcon_query = None
    if (output):
        output = os.path.abspath(output)

    ### ================================= SELECT  ==========================================####
    # Both select and filter options influence whether certain tables need to be joined, the following handles this.

    select = list(select) 
    join = {'joins': set(), 'joined': set()} # Keeping track of what needs to be joined, and what has been joined.
    if multiqc and "sample" not in select:
        select.insert(0, 'sample')
    if sample_description or flowcell_lane or library_id or platform or centre or reference or type or 'sample' in select: 
        join['joins'].add('sample')
    if cohort or cohort_description or 'cohort' in select:
        join['joins'].add('cohort')
    if batch or batch_description or 'batch' in select:
        join['joins'].add('batch')
    if tool_metric or 'tool-metric' in select:
        join['joins'].add('tool-metric')
    [join['joins'].add(s) for s in select]

    with session_scope() as session:
        falcon_query = query_select(session, select, join, tool_metric, multiqc)

    ### ================================= FILTER  ==========================================####

    ## 1. Sample
    if tool_metric:
        falcon_query = query_metric(falcon_query, join, tool_metric)

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
        falcon_query = falcon_query.filter(Sample.centre.in_(centre))

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

    if not multiqc and not csv and not overview:
        # Print result.
        click.echo(query_header)
        for row in falcon_query:
            click.echo(row)

    if overview:
        print_overview(session)

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