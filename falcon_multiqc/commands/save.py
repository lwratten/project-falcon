import click
import json
import datetime
import sys
from os.path import abspath
from database.crud import session_scope
from database.models import Base, RawData, Batch, Sample, Cohort
from sqlalchemy.orm.exc import NoResultFound

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

"""

@click.command()
@click.option("-d", "--directory", type=click.Path(), required=False, help="Path to multiqc_output directory, or provide path to .txt containing list of paths") 
@click.option("-s", "--sample_metadata", type=click.Path(), required=False, help="Sample metadata file, or provide path to .txt containing list of metadata files")
@click.option("-b", "--batch_description", type=click.STRING, required=False, help="Give every new batch this description.")
@click.option("-c", "--cohort_description", type=click.STRING, required=False, help="Give every new cohort this description.")
@click.option("-bm", "--batch_metadata", type=click.File(), required=False, help="Batch metadata file (with descriptions)")
@click.option("-cm", "--cohort_metadata", type=click.File(), required=False, help="Cohort metadata file (with descriptions)")
def cli(directory, sample_metadata, batch_description, cohort_description, batch_metadata, cohort_metadata):
    """Saves the given cohort directory to the falcon_multiqc database"""

    with session_scope() as session:

        if directory or sample_metadata:
            if not(directory and sample_metadata):
                click.echo("Please specify the path to multiqc_output AND path to respective metadata.csv when saving to database")
                sys.exit(1)

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
                directory_name = directory.split('/')[-1]
                sample_metadata_name = sample_metadata.split('/')[-1]
                click.echo(f'Saving: {directory_name} with sample metadata: {sample_metadata_name}...')
                
                with open(directory + "/multiqc_data/multiqc_data.json") as multiqc_data:
                    with open(sample_metadata) as sample_metadata:
                        # Skip header
                        next(sample_metadata)

                        # Keep track of samples added, so we know its primary key, when saving raw data later.
                        samples = {}  # name : primary key id
                        batches = [] # batches within given metadata 

                        # Cohort id for this input. Cohort id must be the same for every batch of this input.
                        cohort_id = None

                        for line in sample_metadata:
                            split = line.split(",")
                            try:
                                sample_name = split[0]
                                batch_name = split[2]
                                flowcell_lane = split[3]
                                library_id = split[4]
                                platform = split[5]
                                centre = split[6]
                                reference = split[7]
                                type = split[8]
                                description = split[9]
                            except IndexError:
                                raise Exception(f"Metadata format is invalid, Accepted format is:"
                                "\n'Sample Name' 'Cohort Name' 'Batch Name' 'Flowcell.Lane' 'Library ID' 'Platform' 'Centre of Sequencing' 'Reference Genome' 'type' 'Description'")

                            if not cohort_id:
                                # Get cohort id / name from the first data row (assuming the metadata is for 1 cohort).
                                cohort_id = split[1]
                                if session.query(Cohort.id).filter_by(id=cohort_id).scalar() is None:
                                    # Cohort does not exist in database.
                                    cohort_row = Cohort(
                                        id=cohort_id,
                                        description=cohort_description
                                    )
                                    session.add(cohort_row)
                            elif split[1] != cohort_id:
                                raise Exception(f"Metadata input has multiple cohort ids ({cohort_id} and {split[1]}). Save supports one cohort at a time.")
                            
                            batch_id = None
                            if batch_name not in batches:
                                # First time this batch_name is seen from this given metadata.csv
                                batches.append(batch_name) 
                                if session.query(Batch.id).filter(Batch.batch_name == batch_name, Batch.cohort_id == cohort_id).scalar() is None:
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
                                    # batch/cohort already existed in database, meaning duplicate entry - envoke traceback.
                                    num_samples = session.query(Sample).join(Batch, Batch.id == Sample.batch_id).filter(Batch.batch_name == batch_name,
                                    Sample.cohort_id == cohort_id).count()
                                    raise Exception(f"Duplicate data entry detected.\nIn metadata file {sample_metadata_name}, batch {batch_name}"
                                        f" from cohort {cohort_id} already exists in the database with {num_samples} sample entries"
                                        f"\nAll entries added from this metadata.csv and its respective multiqc directory {directory_name} during this session will be rollbacked.")
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
                                
                                try:
                                    raw_data_row = RawData(
                                        sample_id=samples[sample_name],
                                        qc_tool=tool[8:],
                                        metrics=multiqc_data_json["report_saved_raw_data"][tool][sample]
                                    )
                                    session.add(raw_data_row)
                                    session.flush()
                                except KeyError:
                                    raise Exception(f"Metadata file {sample_metadata_name} does not match with multiqc folder {directory_name} data JSON file"
                                        f"\nThe sample {sample_name} appears in the JSON, but not in the metadata file."
                                        " Please ensure the metadata file and multiqc directories are from the same batch/cohort."
                                        f"\nAll entries added from this metadata.csv and its respective multiqc directory {directory_name} during this session will be rollbacked.")
                
                click.echo(f"Multiqc folder {directory_name} and metadata {sample_metadata_name} have been saved!\n")
                session.commit() # actually commit (save to db) all rows saved during transaction for given metadata/multic_JSON to database


        # Save batch metadata.
        if batch_metadata:
            # Skip header
            next(batch_metadata)
            for line in batch_metadata:
                split = line.split(",")
                batch_name = split[0]
                number_of_samples = split[1] # to be implmented (have to modify models)
                batch_description = split[2]
                # Update each batch with the given batch description.
                try:
                    (session.query(Batch).filter(Batch.batch_name == batch_name).one().description) = batch_description
                    session.commit()
                    click.echo(f"Batch '{batch_name}' description has been saved.")
                except NoResultFound:
                    click.echo(f"Batch '{batch_name}' is not present in the database so description cannot be added, exiting.")
                    sys.exit(1)

        # Save Cohort metadata.
        if cohort_metadata:
            # Skip header
            next(cohort_metadata)
            for line in cohort_metadata:
                split = line.split(",")
                cohort_name = split[0] # to be implmented (have to modify models)
                number_of_samples = split[1] # to be implmented (have to modify models)
                Number_of_batches = split[2] # to be implmented (have to modify models)
                type = split[3] # to be implmented (have to modify models)
                cohort_description = split[4]
                # Update each Cohort with the given Cohort description.
                try:
                    (session.query(Cohort).filter(Cohort.id == cohort_name).one().description) = cohort_description
                    session.commit()
                    click.echo(f"Cohort '{cohort_name}' description has been saved.")
                except NoResultFound:
                    click.echo(f"Cohort '{cohort_name}' is not present in the database so description cannot be added, exiting.")
                    sys.exit(1)
