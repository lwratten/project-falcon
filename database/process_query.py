import os
import csv
import subprocess 

#temp: example user or query file paths 
# user_path = r"D:\C_DRIVE_DATA\falcon_multiqc_DATA\test"
# query_file = r'C:\Users\New\Desktop\MastersIT\2020T3\BINF6112\Project_Falcon\test2\list_samples.txt'

def process_query(query_file, **kwargs):
    # query_file needs to be absolute path
    # accepted kwargs are: csv, multiqc - can use both at once
    # For each key, value is the absolute path user wants data to be saved
    # By deafult this function will stdout 

    if 'csv' in kwargs.keys():
        with open(query_file, 'r') as metric_list:
            csv_reader = csv.reader(metric_list)
            with open(kwargs['csv'] + '\metrics.csv', 'w') as metric_csv:
                csv_writer = csv.writer(metric_csv, delimiter = ',')
                for line in csv_reader:
                    csv_writer.writerow(line)

    if 'multiqc' in kwargs.keys():   
        config = os.path.abspath("./falconqc.config")
        subprocess.run(['multiqc', '-l', query_file, '-c', config, '-o', kwargs['multiqc']]) #'-c', config,
    
    if not kwargs.keys():
        with open(query_file, 'r') as metric_list:
            csv_reader = csv.reader(metric_list)
            for line in csv_reader:
                print(line)

#temp
#process_query(query_file, csv = user_path, multiqc = user_path)