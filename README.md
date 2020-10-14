# project-falcon
A tool for parsing multiqc reports into a database and querying from the command-line

## User instructions
- The below dev instructions + `falcon_multiqc` command.
- `falcon_multiqc --help` to see all available commands
- `falcon_multiqc create_tables` to create database tables
- `falcon_multiqc create_tables --destroy` destroy old tables and create new database tables
- `falcon_multiqc create_cohort` creates a new cohort in the database and sends its primary key / id to stdout
- `falcon_multiqc save -d path/to/directory -c cohortID` save the directory data to the database and given cohort ID

## Dev instructions
1. `git clone https://github.com/lwratten/project-falcon.git`
2. `cd project-falcon`
3.  Ensure your system has the tools in requirements.system installed.
4. `python3 -m venv env` create a python virtual environment if you haven't already
5. `source env/bin/activate`  activate / go into the virtual environment
6. `pip install --editable .` this allows you to install the tool and updates automatically if you edit it (re-install if you change any of the cli / click things)


### Files
* Directory `falcon_multiqc` contains the core code of the tool.
* Directory `commands` contains Click commands, e.g. save. 
* File `falcon_multiqc/cli.py` sets up Click so it will automatically search the `commands` directory for commands. After installing, run `falcon_multiqc` and see the commands available.
* File `setup.py` allows you to use `pip install --editable .` or `pip install .`.


