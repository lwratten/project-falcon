import click
import glob
import os
from sqlalchemy import create_engine
from database.config import DATABASE_URI
from database.process_query import run_multiqc

# example query: 

# this query will query fastqc tool for Total seqence metric - since only the first batch ran fastqc it will only return first batch
#SELECT s.sample_name, b.path, rd.metrics FROM public.raw_data as rd join sample as s on (s.id = rd.sample_id) join batch as b on (s.batch_id = b.id) where rd.qc_tool = 'fastqc' AND (rd.metrics->>'Total Sequences')::numeric::integer >= 316624794;

# this queries two different tools (picard_insertsize and verifybamid) and on of their respective metrics - returns sampleID from first batch and sampleID from 4012 batch 
# SELECT s.sample_name, b.path FROM public.raw_data as rd join sample as s on (s.id = rd.sample_id) join batch as b on (s.batch_id = b.id) where ((rd.qc_tool = 'picard_insertSize' AND (rd.metrics->>'MEAN_INSERT_SIZE')::numeric::integer <= 390) OR (rd.qc_tool = 'verifybamid' AND (rd.metrics->>'#READS')::numeric::integer >= 4850000));

@click.command()
@click.option("-d", "--directory", type=click.STRING, required=True, help="where query result will be saved")
@click.option("-s", "--sql", type=click.INT, required=False, help="Enter 1 to start SQL querying tool") 
def cli(directory, sql):
    if sql == 1:
        """SQL query tool: ensure all queries SELECT for sample_name from sample table AND path from batch table"""

        count = 0 # to ensure new file name generated
        config = os.path.abspath("./database/falconqc.config") # loading falconqc config file 
        query_eng = create_engine(DATABASE_URI) # establishing engine for communication 
        click.echo("Entering SQL querying tool, to exit type 'exit' as the SQL statement")
        while True:
            sql = click.prompt("Enter SQL query")
            if sql == 'exit':
                break   
            map_path_sample = {} # Dictionary to store path:sampleID key value pairs 
            with query_eng.connect() as conn:
                sample_list = list(conn.execute(sql)) # executes SQL query against database - sample list stores tuples of (path, sampleID)
                click.echo(f"Query complete with {len(sample_list)} samples found, compiling path file for multiqc...")
                for sampleID, path in sample_list:
                    try:
                        map_path_sample[path].append(sampleID) # add sampleID to list of a given path key (a path is generally a batch folder)
                    except KeyError:
                        map_path_sample[path] = [sampleID] # if the path is not a key, make a new key and create a list to store all it's respective sampleIDs
                with open(directory + f'/falconqc_query_{str(count)}.txt', 'w') as file_names: # creates new file to store all sampleID absolute paths 
                    for path in map_path_sample.keys(): # for each batch folder path
                        os.chdir(path) # change directory to path
                        for sampleID in map_path_sample[path]: # go through each sampleID in given batch folder path
                            print(f'sample id is: {sampleID}')
                            for file_name in glob.glob(sampleID + '*'): # find every file assoicated with sampleID
                                file_names.write(path + '/' + file_name + '\n') # write into file
                                #TODO this is the part that takes ages because it's searching sampleID in a folder containing 96,000 files. We need to break up the folder into the 10 batch folders

            run_multiqc(directory + f'/falconqc_query_{str(count)}.txt', config, directory) # run_multiqc function creates new multiqc report
            count += 1
            click.echo("\nNew multiqc report created!\n")
        query_eng.dispose()
