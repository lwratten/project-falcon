import click
from database.crud import engine as query_eng
from database.process_query import create_new_multiqc

# example query: e.g. falcon_multiqc sql -d <path> -s <"sql query"> 
# use quotation marks for the sql query 

# this query will query fastqc tool for Total seqence metric - since only the first batch ran fastqc it will only return first batch
# "SELECT s.sample_name, b.path FROM public.raw_data as rd join sample as s on (s.id = rd.sample_id) join batch as b on (s.batch_id = b.id) where rd.qc_tool = 'fastqc' AND (rd.metrics->>'Total Sequences')::numeric::integer >= 316624794;"

# this queries two different tools (picard_insertsize and verifybamid) and on of their respective metrics - returns sampleID from first batch and sampleID from 4012 batch 
# "SELECT s.sample_name, b.path FROM public.raw_data as rd join sample as s on (s.id = rd.sample_id) join batch as b on (s.batch_id = b.id) where ((rd.qc_tool = 'picard_insertSize' AND (rd.metrics->>'MEAN_INSERT_SIZE')::numeric::integer <= 390) OR (rd.qc_tool = 'verifybamid' AND (rd.metrics->>'#READS')::numeric::integer >= 4850000));"

@click.command()
@click.option("-d", "--directory", type=click.STRING, required=True, help="where query result will be saved")
@click.option("-s", "--sql", type=click.STRING, required=False, help="Enter exact sql query within quotation marks") 
def cli(directory, sql):
    if sql:
        """SQL query tool: ensure all queries SELECT for sample_name from sample table AND path from batch table"""

        click.echo("Processing sql query!") 
        with query_eng.connect() as conn:
            sample_list = list(conn.execute(sql)) # executes SQL query against database - sample list stores tuples of (path, sample_name) 
            click.echo(f"Query complete with {len(sample_list)} samples found, compiling path file for multiqc...")
            create_new_multiqc(sample_list, directory) # create new multiqc report from query 
        query_eng.dispose()
