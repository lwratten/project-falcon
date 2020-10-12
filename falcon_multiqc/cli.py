import os
import click

# ComplexCLI code mainly from Click example.
# https://github.com/pallets/click/blob/master/examples/complex/complex/cli.py#L31
class ComplexCLI(click.MultiCommand):
    def list_commands(self, ctx):
        commands = []
        commands_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "commands"))
        for filename in os.listdir(commands_folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                commands.append(filename.replace(".py", ""))

        commands.sort()
        return commands

    def get_command(self, ctx, name):
        try:
            mod = __import__(f"falcon_multiqc.commands.{name}", None, None, ["cli"])
        except ImportError as e:
            print(e)
            return
        return mod.cli

@click.command(cls=ComplexCLI)
def cli():
    """Welcome to Falcon multiQC!"""
    pass
