import json
from database.crud import session_scope
from database.models import Base, RawData

# Parses the given multiqc_data.json file and adds a Raw_data to the database.


def parse_raw_multiqc_data(file):
    multiqc_data_json = json.load(file)

    with session_scope() as session:

        for tool in multiqc_data_json["report_saved_raw_data"]:
            for sample in multiqc_data_json["report_saved_raw_data"][tool]:
                # TODO: implement adding all Sample, Cohort etc. before adding RawData
                """
                raw_sample = RawData(
                    sample_id=sample,
                    qc_tool=tool.split("_")[1],
                    metrics=multiqc_data_json["report_saved_raw_data"][tool][sample]
                )

                session.add(raw_sample)
                """
