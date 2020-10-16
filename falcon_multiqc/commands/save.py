import click
import json
import datetime
from database.crud import session_scope
from database.models import Base, RawData, Batch, Sample, Cohort


@click.command()
@click.option("-d", "--directory", type=click.Path(), required=True, help="Path to multiqc_output directory")
@click.option("-s", "--sample_metadata", type=click.File(), required=True, help="Sample metadata file")
@click.option("-b", "--batch_description", type=click.STRING, required=False, help="Description of this batch (assuming this is one batch)")
@click.option("-c", "--cohort_description", type=click.STRING, required=False, help="Description of this cohort (assuming this is one cohort)")
def cli(directory, sample_metadata, batch_description, cohort_description):
    """Saves the given directory to the falcon_multiqc database"""
    # TODO: better error handling
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

                if not cohort_id and session.query(Cohort.id).filter_by(id=split[1]).scalar() is None:
                    # Cohort does not exist in database.
                    cohort_row = Cohort(
                        id=split[1],
                        type=split[7],
                        description=cohort_description
                    )
                    session.add(cohort_row)

                # Get cohort id / name from the first data row (assuming the metadata is for 1 cohort).
                if not cohort_id:
                    cohort_id = split[1]

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
                    description=description
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
