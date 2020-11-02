import os
import csv
import subprocess 
import glob

# Creates new csv with the sqlalchemy query result in the given output directory.
def create_csv(query_header, query_result, output_dir):
    with open(output_dir + '/query.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter = ',')

        csv_writer.writerow(query_header)

        for row in query_result:
            csv_writer.writerow(row)
    print("csv report created!")

# Requires list containing tuples in the form (sample_name, path), and requires user specified output directory path 
# Function will find and save all files matching sample_name and return file
def create_new_multiqc(path_sample_list, output_dir):
    map_path_sample = {} # Dictionary to store path:sample_name key value pairs 
    config = os.path.abspath("./database/multiqc.config") # loading falconqc config file
    if type(path_sample_list) != type([]) and type(path_sample_list[0]) != type(()) and len(path_sample_list[0]) != 2:
        raise Exception("Invalid input: this function only accepts lists containing tuples of the form (sample_name, path)")

    if len(path_sample_list) == 0:
        raise Exception("No results from query")

    for sample_name, path in path_sample_list:
        try:
            map_path_sample[path].append(sample_name) # add sample_name to list of a given path key (a path is generally a batch folder)
        except KeyError:
            map_path_sample[path] = [sample_name] # if the path is not a key, make a new key and create a list to store all it's respective sample_names
    with open(output_dir + f'/falconqc_query.txt', 'w') as sample_filenames: # creates new file to store all sample_name absolute paths 
        for path in map_path_sample.keys(): # for each batch folder path
            os.chdir(path) # change directory to path
            for sample_name in map_path_sample[path]: # go through each sample_name in given batch folder path
                for file_name in glob.glob(sample_name + '*'): # find every file assoicated with sample_name
                    sample_filenames.write(path + '/' + file_name + '\n') # write into file
                    #TODO this is the part that takes ages because it's searching sample_name in a folder containing 96,000 files. We need to break up the folder into the 10 batch folders
    
    subprocess.run(['multiqc', '-l', output_dir + f'/falconqc_query.txt', '-c', config, '-o', output_dir]) # run command to create new multiqc report with sample files specified
    print("\nNew multiqc report created!\n")
