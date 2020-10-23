import click
import glob
import os
from database.crud import engine as query_eng
from database.process_query import run_multiqc

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
        map_path_sample = {} # Dictionary to store path:sample_name key value pairs 
        config = os.path.abspath("./database/falconqc.config") # loading falconqc config file
        with query_eng.connect() as conn:
            sample_list = conn.execute(sql) # executes SQL query against database - sample list stores tuples of (path, sample_name)
            click.echo(f"Query complete with {sample_list.rowcount} samples found, compiling path file for multiqc...")
            for row in sample_list:
                try:
                    map_path_sample[row['path']].append(row['sample_name']) # add sample_name to list of a given path key (a path is generally a batch folder)
                except KeyError:
                    map_path_sample[row['path']] = [row['sample_name']] # if the path is not a key, make a new key and create a list to store all it's respective sample_names
            with open(directory + f'/falconqc_query.txt', 'w') as file_names: # creates new file to store all sample_name absolute paths 
                for path in map_path_sample.keys(): # for each batch folder path
                    os.chdir(path) # change directory to path
                    for sample_name in map_path_sample[path]: # go through each sample_name in given batch folder path
                        print(f'sample id is: {sample_name}')
                        for file_name in glob.glob(sample_name + '*'): # find every file assoicated with sample_name
                            file_names.write(path + '/' + file_name + '\n') # write into file
                            #TODO this is the part that takes ages because it's searching sample_name in a folder containing 96,000 files. We need to break up the folder into the 10 batch folders
    
        run_multiqc(directory + f'/falconqc_query.txt', config, directory) # run_multiqc function creates new multiqc report
        click.echo("\nNew multiqc report created!\n")
    query_eng.dispose() #TODO I don't know whether to dispose this or not? 
