import os
import csv
import subprocess 
import glob
import click
import sys

# Creates new csv with the sqlalchemy query result in the given output directory.
def create_csv(query_header, query_result, output_path, filename):
    with open(f"{output_path}/{filename}.csv", 'w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter = ',')

        csv_writer.writerow(query_header)

        for row in query_result:
            csv_writer.writerow(row)

# Prints query result in csv format to stdout.
def print_csv(query_header, query_result):
    csv_writer = csv.writer(sys.stdout)
    csv_writer.writerow(query_header)
    for row in query_result:
        csv_writer.writerow(row)

# Requires list containing tuples in the form (sample_name, path), and requires user specified output directory path 
# Function will find and save all files matching sample_name and return file
def create_new_multiqc(path_sample_list, output_dir, filename):
    map_path_sample = {} # Dictionary to store path:sample_name key value pairs 
    config = os.path.join(os.path.dirname(__file__) , 'multiqc.config') # loading falconqc config file
    output_name = filename + "_multiqc_report"

    if type(path_sample_list) != type([]) and type(path_sample_list[0]) != type(()) and len(path_sample_list[0]) != 2:
        raise Exception("Invalid input: this function only accepts lists containing tuples of the form (sample_name, path)")

    if len(path_sample_list) == 0:
        raise Exception("No results from query")

    for sample_name, path in path_sample_list:
        try:
            map_path_sample[path].append(sample_name) # add sample_name to list of a given path key (a path is generally a batch folder)
        except KeyError:
            map_path_sample[path] = [sample_name] # if the path is not a key, make a new key and create a list to store all it's respective sample_names
    
    with open(output_dir + "/falconqc_query.txt", 'w') as sample_filenames: # creates new file to store all sample_name absolute paths 
        for path in map_path_sample.keys(): # for each batch folder path
            os.chdir(path) # change directory to path
            for sample_name in map_path_sample[path]: # go through each sample_name in given batch folder path
                for file_name in glob.glob(sample_name + '*'): # find every file assoicated with sample_name
                    sample_filenames.write(path + '/' + file_name + '\n') # write into file

    # Run command to create new multiqc report with sample files specified
    process = subprocess.run(['multiqc', '-l', output_dir + '/falconqc_query.txt', '-c', config, '-o', output_dir, '-n', output_name])

    # Remove temp sample_filenames file
    os.remove(output_dir + "/falconqc_query.txt")

    if (process.returncode == 0):
        click.echo(f"New multiqc report created in {output_dir} as '{output_name}.html'.")
    else:
        click.echo(click.style("Failed to create multiqc report.", fg="red"))
