import click
import json
import csv
import datetime
import sys
from os.path import abspath
from database.crud import session_scope
from database.models import Base, RawData, Batch, Sample, Cohort

"""
This command saves input multiqc data to the falcon multiqc database.
It supports saving 1 cohort at a time.

Required Arguments:
    directory {path/file} -- Multiqc cohort directory to save. May also be a list of directories.

    sample_metadata {file} -- A csv with the header (or list of paths to sample_metadata files):
    "Sample,Name,Cohort,Name,Batch,Name,Flowcell.Lane,Library ID,Platform,Centre of Sequencing,Reference Genome,Type,Description"

Optional Description Arguments:
    batch_description {string} -- Set this if the input is 1 batch.
    cohort_description {string} -- Set this if the input is 1 cohort.
    batch_metadata {file} -- A csv with header "Batch Name,Description". Set this if the input is multiple batches.
    csv {file} -- a csv with directories and sample_metadata for bulk saving. If this option is used --directory and --sample_metadata are not required.

"""


def save_sample(directory, sample_metadata, session, cohort_description, batch_description):
    """Saves one result directory and sample_metadatadata to the falcon_multiqc database"""
    click.echo(f'Saving: {directory} with sample metadata: {sample_metadata}...')
            
    # Cohort id for this input. Cohort id must be the same for every batch of this input.
    cohort_id = None

    with open(directory + "/multiqc_data/multiqc_data.json") as multiqc_data:
        with open(sample_metadata) as sample_metadata:
            # Skip header
            next(sample_metadata)

            # Keep track of samples added, so we know its primary key, when saving raw data later.
            samples = {}  # name : primary key id

            for line in sample_metadata:
                split = line.split(",")
                sample_name = split[0]
                batch_name = split[2]
                flowcell_lane = split[3]
                library_id = split[4]
                platform = split[5]
                centre = split[6]
                reference = split[7]
                type = split[8]
                description = split[9]

                batch_id = None

                if not cohort_id:
                    # Get cohort id / name from the first data row (assuming the metadata is for 1 cohort).
                    cohort_id = split[1]
                    if session.query(Cohort.id).filter_by(id=split[1]).scalar() is None:
                        # Cohort does not exist in database.
                        cohort_row = Cohort(
                            id=split[1],
                            description=cohort_description
                        )
                        session.add(cohort_row)
                elif split[1] != cohort_id:
                    raise Exception(f"Input has multiple cohort ids ({cohort_id} and {split[1]}). Save supports one cohort at a time.")

                if session.query(Batch).filter(Batch.batch_name == batch_name, Batch.cohort_id == cohort_id).scalar() is None:
                    # Batch does not exist in database.
                    batch_row = Batch(
                        cohort_id=cohort_id,
                        batch_name=batch_name,
                        path=abspath(directory),
                        description=batch_description
                    )
                    session.add(batch_row)
                    session.flush()
                    batch_id = batch_row.id
                else:
                    batch_id = session.query(Batch).filter(
                        Batch.batch_name == batch_name, Batch.cohort_id == cohort_id).one().id

                sample_row = Sample(
                    batch_id=batch_id,
                    cohort_id=cohort_id,
                    sample_name=sample_name,
                    flowcell_lane=flowcell_lane,
                    library_id=library_id,
                    platform=platform,
                    centre=centre,
                    reference_genome=reference,
                    description=description,
                    type=type
                )
                session.add(sample_row)
                session.flush()
                samples[sample_name] = sample_row.id

            multiqc_data_json = json.load(multiqc_data)

            for tool in multiqc_data_json["report_saved_raw_data"]:
                for sample in multiqc_data_json["report_saved_raw_data"][tool]:
                    sample_name = sample.split("_")[0]

                    raw_data_row = RawData(
                        sample_id=samples[sample_name],
                        qc_tool=tool[8:],
                        metrics=multiqc_data_json["report_saved_raw_data"][tool][sample]
                    )
                    session.add(raw_data_row)

# Defining the callback function for --input_csv
def print_csv(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    # Check we actually have a csv
    if value[-4:] == '.csv':

        # Check the headers of the csv are directory,sample_metadata
        # open file in read mode
        with open(value, 'r') as input_csv:
            # pass the file object to reader() to get the reader object
            csv_reader = csv.reader(input_csv)
            header = next(csv_reader)

            # check the header
            if header[0] == "directory" and header[1] == "sample_metadata":
                with session_scope() as session:
                    # TODO - save the data!
                    # Iterate over each row in the csv using reader object
                    for row in csv_reader:
                        # row variable is a list that represents a row in csv
                        print(row)
                        save_sample(row[0], row[1], session)
                    sys.exit(0)
            else:
                click.echo("CSV requires directory and sample_metadata headers.")
                sys.exit(1)
    else:
        click.echo("A csv file is required when using the --input_csv flag.")
        sys.exit(1)



@click.command()
@click.option("-d", "--directory", type=click.Path(exists=True), required=True, help="Path to multiqc_output directory.") 
@click.option("-s", "--sample_metadata", type=click.Path(exists=True), required=True, help="Sample metadata file.")
@click.option("-i", "--input_csv", type=click.Path(exists=True), required=False, callback=print_csv, is_eager=True, help="CSV file with directories and sample metadata paths for bulk saving. If this option is selected, directory and sample_metadata are not required")
@click.option("-b", "--batch_description", type=click.STRING, required=False, help="Give every new batch this description.")
@click.option("-c", "--cohort_description", type=click.STRING, required=False, help="Give every new cohort this description.")
@click.option("-bm", "--batch_metadata", type=click.File(), required=False, help="Batch metadata file (with descriptions).")

def cli(directory, sample_metadata, input_csv, batch_description, cohort_description, batch_metadata):
    """Saves the given cohort directory to the falcon_multiqc database"""

    with session_scope() as session:

        # Check if directory is a list of directories/metadata files.
        if directory[-4:] == '.txt':
            with open(directory) as dir_list:
                batch_dir_list = [d[:-1] for d in dir_list]

            if sample_metadata[-4:] == '.txt':
                with open(sample_metadata) as file_list:
                    metadata_file_list = [d[:-1] for d in file_list]
            else:
                click.echo("If list of batch dir are provided, corresponding list of metadata files are required.")
                sys.exit(1)

            if len(batch_dir_list) != len(metadata_file_list):
                click.echo("Warning, provided list of directories do not match corresponding list of metadata files.")
                sys.exit(1)
        else: # Default: when a single directory or file is provided
            batch_dir_list = [directory]
            metadata_file_list = [sample_metadata]
        
        for i in range(len(batch_dir_list)):
            directory = batch_dir_list[i]
            sample_metadata = metadata_file_list[i]

            save_sample(directory, sample_metadata, session, cohort_description, batch_description)

        # Save batch metadata.
        if batch_metadata:
            # Skip header
            next(batch_metadata)
            for line in batch_metadata:
                split = line.split(",")
                batch_name = split[0]
                batch_description = split[2]
                # Update each batch with the given batch description.
                (session.query(Batch)
                    .filter(Batch.batch_name == batch_name, Batch.cohort_id == cohort_id)
                    .one().description) = batch_description
