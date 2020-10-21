# project-falcon
A tool for parsing multiqc reports into a database and querying from the command-line

## User instructions
- The below dev instructions + `falcon_multiqc` command.
- Use `falcon_multiqc --help` to see all available commands
### Save commands
- Use `falcon_multiqc save --help` to see how to use save.
- `falcon_multiqc save --directory multiqc/output/path --sample_metadata meta_data_file
- `--sample_metadata` is a required argument - A csv with the header: `Sample,Name,Cohort,Name,Batch,Name,Flowcell.Lane,Library ID,Platform,Centre of Sequencing,Reference Genome,Type,Description`
- Adding descriptions to cohort, batch, or sample is optional.
  - `--batch_description` {string} -- Set this if the input is 1 batch. Will apply this description to all new batches.
  - `--cohort_description` {string} -- Set this if the input is 1 cohort. Will apply this description to all new cohorts.
  - `--batch_metadata` {file} -- A csv with header `Batch Name,Description`. Set this if the input is multiple batches.


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


