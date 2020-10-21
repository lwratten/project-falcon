import os
import csv
import subprocess 

# Creates new multiqc report given the absolute path for file_names.txt and the user specified directory
def run_multiqc(file_names, user_dir, html = None):
    config = os.path.abspath("./falconqc.config")
    subprocess.run(['multiqc', '-l', file_names, '-c', config, '-o', user_dir]) 
    if html:
        subprocess.call(['xdg-open', user_dir + '/multiqc_report.html']) # for windows: os.startfile(user_dir + '\multiqc_report.html')

# Creates new csv files given the metric_list (not sure what this is yet) and the abolute path for the user specified directory 
def create_csv(metric_list, user_dir):
    with open(metric_list, 'r') as ml:
        csv_reader = csv.reader(ml)
        with open(user_dir + '\metrics.csv', 'w') as metrics_csv:
            csv_writer = csv.writer(metrics_csv, delimiter = ',')
            for line in csv_reader:
                csv_writer.writerow(line)

# Prints the list of samples (as row) returned from query 
def print_query(sample_list, user_dir):
    [print(sample_list[i]) for i in sample_list]

