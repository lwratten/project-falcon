import click
import sys
import os
from database.crud import session_scope
from database.process_query import create_new_multiqc, create_csv, print_csv
from .query import print_overview
from tabulate import tabulate

"""
This command allows you to query the falcon multiqc database using raw SQL.

Options:

-s --sql <path.txt> Enter path (relative or absolute) to .txt containing raw SQL statement
    See example_1, example_2, example_3 for examples

-o --output <path> Specify the directory to save either your csv or multiqc result when using the --csv or --multiqc options

-f --filename <filename> Name (no extensions) the csv or multiqc html report when using the --csv or --multiqc options

-c --csv Creates csv file in output directory from query result 
    See example_2, example_3

-m --multiqc Use this flag to generate a multiqc report from query, saved in output directory. 
    See example_3
    NOTE: To use, you must make sure to select for 'sample.sample_name' AND 'batch.path'
          Do not specify an alias, just do: SELECT sample.sample_name, batch.path
    NOTE: To select for 'sample.sample_name' AND 'batch.path' you must join batch table with sample table

--overview Prints an overview of the number of samples in each batch/cohort.

NOTE: If --multiqc or --csv flags are not used, result will print to stdout as csv.

Example_1 (Stdout): 
`falcon_multiqc sql --sql sql.txt`

Where sql.txt contains the following:

    SELECT s.sample_name, rd.qc_tool, s.cohort_id, b.batch_name FROM public.raw_data as rd 
    join sample as s on (s.id = rd.sample_id)
    join batch as b on (b.id = s.batch_id)
    where 
    (s.id in (
                    SELECT rd.sample_id FROM public.raw_data as rd 
                    where (
                        (rd.qc_tool = 'verifybamid' AND (rd.metrics->>'AVG_DP')::numeric::float < 30)
                        OR 
                        (rd.qc_tool = 'picard_insertSize' AND (rd.metrics->>'MEAN_INSERT_SIZE')::numeric::float > 410)
                        OR 
                        (rd.qc_tool = 'picard_wgsmetrics' AND (rd.metrics->>'PCT_EXC_DUPE')::numeric::float <= 0.0921)
                        )
                    group by rd.sample_id
                    having count(rd.sample_id) >= 3
                )
    )
    order by s.sample_name

Example_2 (CSV):
`falcon_multiqc sql --sql sql2.txt --csv --output your/output/directory --filename your_csv_report`

Where sql2.txt contains the following:

    SELECT sample.id AS sample_id, 
    sample.sample_name AS sample_sample_name,
    max(raw_data.metrics ->> 'AVG_DP') AS AVG_DP, 
    max(raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS MEAN_INSERT_SIZE 
    FROM sample JOIN batch ON sample.batch_id = batch.id JOIN raw_data ON sample.id = raw_data.sample_id 
    WHERE (raw_data.qc_tool='verifybamid' AND CAST((raw_data.metrics ->> 'AVG_DP') AS FLOAT) < 28) 
    OR (raw_data.qc_tool='picard_insertSize' AND CAST((raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS FLOAT) > 490) 
    GROUP BY sample.id, batch.path HAVING count(distinct raw_data.qc_tool) = 2


Example_3 (Multiqc and csv)
`falcon_multiqc sql --sql sql3.txt --multiqc --csv --output output --filename your_multiqc_report`

Where sql2.txt contains the following (need to select for both sample.sample_name AND batch.path when using --multiqc flag): 

    SELECT sample.sample_name,
    batch.path,
    max(raw_data.metrics ->> 'AVG_DP') AS AVG_DP, 
    max(raw_data.metrics ->> '#READS') AS READS, 
    max(raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS MEAN_INSERT_SIZE, 
    max(raw_data.metrics ->> 'PCT_EXC_DUPE') AS PCT_EXC_DUPE 
    FROM sample JOIN batch ON sample.batch_id = batch.id JOIN raw_data ON sample.id = raw_data.sample_id 
    WHERE (raw_data.qc_tool='verifybamid' AND CAST((raw_data.metrics ->> 'AVG_DP') AS FLOAT) < 30 AND CAST((raw_data.metrics ->> '#READS') AS FLOAT) < 2469490) 
    OR (raw_data.qc_tool='picard_insertSize' AND CAST((raw_data.metrics ->> 'MEAN_INSERT_SIZE') AS FLOAT) > 420) 
    OR (raw_data.qc_tool = 'picard_wgsmetrics' AND CAST((raw_data.metrics->>'PCT_EXC_DUPE') AS float) <= 0.0921)
    GROUP BY sample.id, batch.path HAVING count(distinct raw_data.qc_tool) = 3

"""

@click.command()
@click.option("-s", "--sql", type=click.Path(exists=True), required=False, help="Path to txt containing correct raw SQL") 
@click.option("-o", "--output", type=click.STRING, required=False, help="where query result will be saved")
@click.option("-f", "--filename", required=False, help="Output filename (required when --csv or --multiqc).")  
@click.option("-m", "--multiqc", is_flag=True, required=False, help="Create a multiqc report.")
@click.option("-c", "--csv", is_flag=True, required=False, help="Create a csv report.")
@click.option("--overview", is_flag=True, required=False, help="Prints an overview of the number of samples in each batch/cohort.")
def cli(output, filename, sql, multiqc, csv, overview):
    """SQL query tool: ensure all queries SELECT for sample_name from sample table AND path from batch table"""

    if (multiqc or csv) and not output:
        click.echo("When using multiqc or csv option, please specify a directory to save in using the -o option.")
        sys.exit(1)
 
    if (output):
        output = os.path.abspath(output)
        if (not os.path.exists(output)):
            raise Exception(f"Output path {output} does not exist.") 
        if (not os.path.isdir(output)):
            raise Exception(f"Output path {output} is NOT a directory. Please use a directory path with --output.")
        if not filename:
            raise Exception("--output requires --filename (no extension) to name the csv or multiqc report")

    click.echo("Processing sql query!") 
    with session_scope() as session:
        if sql:
            if sql[-4:] != '.txt':
                click.echo("When using --sql option, please supply path to .txt containing the raw SQL statement like in the examples.")
                sys.exit(1)
            sql = os.path.abspath(sql)
            with open(sql) as sql_file:
                # Copy raw SQL statement as string.
                sql = '\n'.join(sql_file.readlines())
            
            falcon_query = session.execute(sql) # Executes SQL query against database.
            query_header = falcon_query.keys() # Create header from the current query (falcon_query).
            click.echo(f"Query returned {falcon_query.rowcount} samples.")

            if multiqc:
                if len([col for col in query_header if 'sample_name' in col or 'path' in col]) == 2:
                    click.echo("Creating multiqc report...")
                    create_new_multiqc([(row.sample_name, row.path) for row in falcon_query], output, filename)
                else:
                    click.echo("When using --multiqc option, please select for sample.sample_name AND batch.path (see example_3).")
                    sys.exit(1)

            if csv:
                click.echo("Creating csv report...")
                create_csv(query_header, falcon_query, output, filename)

            if not multiqc and not csv and not overview:
                # Print result.
                click.echo(tabulate(falcon_query, query_header, tablefmt="pretty"))       

        if overview:
            print_overview(session)
