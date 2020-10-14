import click

from .. import parse

# Command for saving data. May have more sub commands in future (see click groups).
@click.command()
@click.option("-d", "--directory", type=click.Path(), help="Path to multiqc_output directory")
def cli(directory):
    """Saves the given directory to the falcon_multiqc database"""

    with open(directory + "/multiqc_data/multiqc_data.json") as multiqc_data:
        parse.parse_raw_multiqc_data(multiqc_data)
