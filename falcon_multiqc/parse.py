import json

# Parses the given multiqc_data.json file and prints it out.
# TODO: Implement saving of this data.
def parse_multiqc_data(file):
    multiqc_data_json = json.load(file)

    for tool in multiqc_data_json["report_saved_raw_data"]:
        print("Tool: " + tool)
        for sample in multiqc_data_json["report_saved_raw_data"][tool]:
            print("\n  Sample: " + sample)

            for metric in multiqc_data_json["report_saved_raw_data"][tool][sample]:
                print("    Metric: " + metric + " = " + str(multiqc_data_json["report_saved_raw_data"][tool][sample][metric]))
        print("---- \n")
