import click
import json
import datetime
from database.crud import session_scope
from database.models import Base, RawData, Batch, Sample


@click.command()
@click.option("-d", "--directory", type=click.Path(), required=True, help="Path to multiqc_output directory")
@click.option("-c", "--cohort", type=click.INT, required=True, help="Id of this batch's cohort (use create_cohort if you need a new one)")
def cli(directory, cohort):
    """Saves the given directory to the falcon_multiqc database"""

    with open(directory + "/multiqc_data/multiqc_data.json") as multiqc_data:
        multiqc_data_json = json.load(multiqc_data)

        with session_scope() as session:
            batch_row = Batch(
                cohort_id=cohort,
                flow_cell_id=0,  # TODO: implement real flow cell id
                path=directory,
                date=datetime.datetime.now()  # TODO: implement real date
            )

            session.add(batch_row)
            session.flush()

            # Keep track of samples added, so we don't duplicate any.
            samples = {}  # name : primary key id

            for tool in multiqc_data_json["report_saved_raw_data"]:
                for sample in multiqc_data_json["report_saved_raw_data"][tool]:
                    sample_id = None
                    # Check if this sample name has already been stored.
                    if not sample in samples:
                        sample_row = Sample(
                            batch_id=batch_row.id,
                            cohort_id=cohort,
                            sample_name=sample
                        )
                        session.add(sample_row)
                        session.flush()
                        samples[sample] = sample_row.id
                        sample_id = sample_row.id
                    else:
                        sample_id = samples[sample]

                    raw_data_row = RawData(
                        sample_id=sample_id,
                        qc_tool=tool.split("_")[1],
                        metrics=multiqc_data_json["report_saved_raw_data"][tool][sample]
                    )
                    session.add(raw_data_row)
