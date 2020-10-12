import click

from .. import parse

# Command for saving data. May have more sub commands in future (see click groups).
@click.command()
@click.option("-f", "--file", type=click.File('r'), help="Path to multiqc_data.json output file")
def cli(file):
    """Command line interface for saving to falcon_multiqc"""
    parse.parse_multiqc_data(file)
