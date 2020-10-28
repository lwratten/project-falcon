# project-falcon
A tool for parsing multiqc reports into a database and querying from the command-line

## User instructions
- The below dev instructions + `falcon_multiqc` command.
- Use `falcon_multiqc --help` to see all available commands

### Save command
- Use `falcon_multiqc save --help` to see how to use save.
- E.g. `falcon_multiqc save --directory multiqc/output/path --sample_metadata meta_data_file`
- `--sample_metadata` is a required argument - A csv with the header: `Sample,Name,Cohort,Name,Batch,Name,Flowcell.Lane,Library ID,Platform,Centre of Sequencing,Reference Genome,Type,Description`
- Adding descriptions to cohort, batch, or sample is optional.
  - `--batch_description` {string} -- Set this if the input is 1 batch. Will apply this description to all new batches.
  - `--cohort_description` {string} -- Set this if the input is 1 cohort. Will apply this description to all new cohorts.
  - `--batch_metadata` {file} -- A csv with header `Batch Name,Description`. Set this if the input is multiple batches.

### Query command
This command allows you to query the falcon multiqc database.

- Select columns to include in output (sample [default], batch, cohort, tool-metric).
    `--select <sample>`
    (Add multiple selections by using multiple `--select` options)

- Add optional filtering with `--batch`, `--cohort`, or `--tool_metric`.
    - `--batch <batch name>`
    - `--cohort <cohort id>`
    - `--tool-metric <tool name> <metric> <operator> <value>`
    (Add multiple filters by using multiple `--batch` / `--cohort` / `--tool-metric' options)

- Note (--tool_metric): 
    - You must always specify 4 values. If <operator> is not valid, this is okay and the output will have the <metric> - with no filtering.
      
      - e.g. `falcon_multiqc query --tool_metric verifybamid AVG_DP '<' 28 -o path`

      - e.g. `falcon_multiqc query --tool_metric verifybamid AVG_DP 0 0 -o path` will select verifybamid AVG_DP in output
    

    - `--tool metric` *MUST be the first argument* to falcon_multiqc query.

    - Special characters must be escaped (wrapped in single quotes) in bash, like '<'.

- Specify output directory with `--output or -o`. 

- Specify output type with either `--csv` or `--multiqc`.
   - Default output is stdout.


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


