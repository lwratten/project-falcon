import click
import json
import datetime
from database.crud import session_scope
from database.models import Base, RawData, Batch, Sample, Cohort

"""
This command saves input multiqc data to the falcon multiqc database.

Required Arguments:
    directory {path} -- Multiqc directory to save.

    sample_metadata {file} -- A csv with the header:
    "Sample,Name,Cohort,Name,Batch,Name,Flowcell.Lane,Library ID,Platform,Centre of Sequencing,Reference Genome,Type,Description"

Optional Description Arguments:
    batch_description {string} -- Set this if the input is 1 batch.
    cohort_description {string} -- Set this if the input is 1 cohort.
    batch_metadata {file} -- A csv with header "Batch Name,Description". Set this if the input is multiple batches.

"""

@click.command()
@click.option("-d", "--directory", type=click.Path(), required=True, help="Path to multiqc_output directory")
@click.option("-s", "--sample_metadata", type=click.File(), required=True, help="Sample metadata file")
@click.option("-b", "--batch_description", type=click.STRING, required=False, help="Give every new batch this description.")
@click.option("-c", "--cohort_description", type=click.STRING, required=False, help="Give every new cohort this description.")
@click.option("-bm", "--batch_metadata", type=click.File(), required=False, help="Batch metadata file (with descriptions)")
def cli(directory, sample_metadata, batch_description, cohort_description, batch_metadata):
    """Saves the given directory to the falcon_multiqc database"""
    with open(directory + "/multiqc_data/multiqc_data.json") as multiqc_data:
        # Skip header
        next(sample_metadata)
        with session_scope() as session:
            # Keep track of samples added, so we know its primary key, when saving raw data later.
            samples = {}  # name : primary key id
            cohort_id = None

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

                if session.query(Batch).filter(Batch.batch_name == batch_name, Batch.cohort_id == cohort_id).scalar() is None:
                    # Batch does not exist in database.
                    batch_row = Batch(
                        cohort_id=cohort_id,
                        batch_name=batch_name,
                        path=directory,
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

            if batch_metadata:
                for line in batch_metadata:
                    split = line.split(",")
                    batch_name = split[0]
                    batch_description = split[1]
                    # Update each batch with the given batch description.
                    session.query(Batch).filter(Batch.batch_name == batch_name, Batch.cohort_id == cohort_id).description = batch_description
