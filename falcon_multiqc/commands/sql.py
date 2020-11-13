import click
import sys
import os
from collections import defaultdict 
from database.crud import session_scope
from database.process_query import create_new_multiqc, create_csv
from .query import print_overview

"""
This command allows you to query the falcon multiqc database using raw SQL.

Options:

-o --output <path> Optionally specify the directory to save either your csv or multiqc result

-s --sql <path> Enter path (relative or absolute) to .txt containing correct raw SQL statement
    See example_1, example_2, example_3  

--multiqc Use this flag to generate a multiqc report from query, saved in output directory. 
    NOTE: To use, you must make sure to select for 'sample.sample_name' AND 'batch.path'
    NOTE: To select for 'sample.sample_name' AND 'batch.path' you must join batch table with sample table
    NOTE: see example_3 for using --multiqc flag

--csv Creates csv file in output directory from query result 
    Example: falcon_multiqc sql --sql sql3.txt --csv

--overview Prints an overview of the number of samples in each batch/cohort.

NOTE: if --multiqc or --csv flags are not used, result will print to stdout


Example_1: 
falcon_multiqc sql --sql sql.txt 

Where sql.txt contains:

    SELECT s.sample_name, rd.qc_tool, s.cohort_id, b.batch_name FROM public.raw_data as rd 
    join sample as s on (s.id = rd.sample_id)
    join batch as b on (b.id = s.batch_id)
    where 
    (s.id in (
                    SELECT rd.sample_id FROM public.raw_data as rd 
                    where (
                        (rd.qc_tool = 'verifybamid' AND (rd.metrics->>'AVG_DP')::numeric::float < 30)
                        OR 
                        (rd.qc_tool = 'picard_insertSize' AND (rd.metrics->>'MEAN_INSERT_SIZE')::numeric::float > 460)
                        OR 
                        (rd.qc_tool = 'picard_wgsmetrics' AND (rd.metrics->>'PCT_EXC_DUPE')::numeric::float <= 0.0921)
                        )
                    group by rd.sample_id
                    having count(rd.sample_id) >= 3
                )
    )
    and s.cohort_id = 'MGRB'
    order by s.sample_name

Example_2:
falcon_multiqc sql --sql sql2.txt 

Where sql2.txt contains: 

    SELECT sample.id AS sample_id, 
    sample.sample_name AS sample_sample_name,
    max(raw_data.metrics ->> 'AVG_DP') AS AVG_DP, 
    max(raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS MEAN_INSERT_SIZE 
    FROM sample JOIN batch ON sample.batch_id = batch.id JOIN raw_data ON sample.id = raw_data.sample_id 
    WHERE (raw_data.qc_tool='verifybamid' AND CAST((raw_data.metrics ->> 'AVG_DP') AS FLOAT) < 28) 
    OR (raw_data.qc_tool='picard_insertSize' AND CAST((raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS FLOAT) > 490) 
    GROUP BY sample.id, batch.path HAVING count(distinct raw_data.qc_tool) = 2


Example_3:
falcon_multiqc sql --sql sql3.txt --multiqc 

Where sql2.txt contains (needs to select for both sample.sample_name AND batch.path): 

    SELECT sample.sample_name AS sample_sample_name,
    batch.path AS batch_path,
    max(raw_data.metrics ->> 'AVG_DP') AS AVG_DP, 
    max(raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS MEAN_INSERT_SIZE 
    FROM sample JOIN batch ON sample.batch_id = batch.id JOIN raw_data ON sample.id = raw_data.sample_id 
    WHERE (raw_data.qc_tool='verifybamid' AND CAST((raw_data.metrics ->> 'AVG_DP') AS FLOAT) < 28) 
    OR (raw_data.qc_tool='picard_insertSize' AND CAST((raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS FLOAT) > 490) 
    GROUP BY sample.id,  HAVING count(distinct raw_data.qc_tool) = 2

"""

@click.command()
@click.option("-s", "--sql", type=click.Path(exists=True), required=True, help="Path to txt containing correct raw SQL") 
@click.option("-o", "--output", type=click.STRING, required=False, help="where query result will be saved")
@click.option("--multiqc", is_flag=True, required=False, help="Create a multiqc report.")
@click.option("--csv", is_flag=True, required=False, help="Create a csv report.")
@click.option("--overview", is_flag=True, required=False, help="Prints an overview of the number of samples in each batch/cohort.")
def cli(output, sql, multiqc, csv, overview):
    """SQL query tool: ensure all queries SELECT for sample_name from sample table AND path from batch table"""

    if (multiqc or csv) and not output:
        click.echo("When using multiqc or csv option, please specify a directory to save in using the -o option")
        sys.exit(1)
 
    if (output):
        output = os.path.abspath(output)

    click.echo("Processing sql query!") 

    sql = os.path.abspath(sql)
    with open(sql) as sql_file:
        sql = '\n'.join(sql_file.readlines())

    with session_scope() as session:
        falcon_query = session.execute(sql) # Executes SQL query against database.
        query_header = falcon_query.keys() # Create header from the current query (falcon_query).
        query_size = falcon_query.rowcount
        click.echo(f"Query resulted in {query_size} samples.")

        if multiqc:
            sample_path = [col for col in query_header if 'sample_name' in col or 'path' in col]
            if len(sample_path) ==2:
                sample_name = [col for col in sample_path if 'sample_name' in col][0] # get the column same for sample.sample_name the user specified 
                path = [col for col in sample_path if 'path' in col][0] # get the column same for batch.path the user specified 
                mapper = defaultdict(list)
                [mapper[key].append(value) for row in falcon_query for key, value in row.items() if 'sample_name' in key or 'path' in key]
                click.echo("Creating multiqc report...")
                create_new_multiqc([(mapper[sample_name][i], mapper[path][i]) for i in range(query_size)], output)

        if csv:
            click.echo("Creating csv report...")
            create_csv(query_header, falcon_query, output)

        if not multiqc and not csv and not overview:
            # Print result.
            click.echo(query_header)
            [click.echo(row) for row in falcon_query]            

        if overview:
            print_overview(session)
