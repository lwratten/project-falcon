# falcon-multiqc
A tool for parsing multiqc reports into a database with querying and charting capabilities from the command-line

## User instructions
- The below dev instructions + `falcon_multiqc` command.
- Use `falcon_multiqc --help` to see all available commands

### Commands
- TODO table of contents
#### 1. Connect 
This command connects the user to a postgres database and creates a new database if one doesn't exist.

- Use `falcon_multiqc connect --help` to see how to use the connect command.
- E.g. `falcon_multiqc connect` will prompt you to enter your username and password and connect to the database.
- Optional Parameters:
  - `--uri` <Database URI> -- Enter a URI to connect to the database with (URI in the form `postgres+psycopg2://USERNAME:PASSWORD@IP_ADDRESS:PORT/DATABASE_NAME`).
  - `--skip-check` -- Skip checking file paths in the database when connecting to an existing database

#### 2. Save
- Use `falcon_multiqc save --help` to see how to use save.
- E.g. `falcon_multiqc save --directory multiqc/output/path --sample_metadata meta_data_file`
- `--sample_metadata` is a required argument - A csv with the header: `Sample,Name,Cohort,Name,Batch,Name,Flowcell.Lane,Library ID,Platform,Centre of Sequencing,Reference Genome,Type,Description`
- Adding descriptions to cohort, batch, or sample is optional.
  - `--batch_description` {string} -- Set this if the input is 1 batch. Will apply this description to all new batches.
  - `--cohort_description` {string} -- Set this if the input is 1 cohort. Will apply this description to all new cohorts.
  - `--batch_metadata` {file} -- A csv with header `Batch Name,Description`. Set this if the input is multiple batches.

#### 3. Query
This command allows you to query the falcon multiqc database.

- Select columns to include in output (sample [default], batch, cohort, tool-metric).
    `--select <sample>`
    (Add multiple selections by using multiple `--select` options)

- Add optional filtering with (all behave like OR when multiple of the same filter, except for `--tool-metric` which behaves like AND):

    - Cohort Filtering:
      - `--cohort <cohort id>` 
      - `--cohort-description <"description">` (contains)

    - Batch Filtering:
      - `--batch <batch name>`
      - `--batch-description <"description">` (contains)
      
    - Sample filtering:
      - `--tool-metric <tool name> <metric> <operator> <value>` (behaves like **AND** when multiple)
      - `--sample-description <"description">` (contains)
      - `--flowcell-lane <sample flow cell name>` 
      - `--library-id <sample library id>` 
      - `--centre <sample centre>` 
      - `--reference <sample reference genome>` 
      - `--type <sample type>` 
      - `--platform <sample platform>` 

    (Add multiple filters by using multiple `--batch` / `--cohort` / `--tool-metric' etc. options)
    
- Note (`--tool-metric`): 
    - You must always specify 4 values. 
    
    If any <operator> is not valid, output will have the <metric>/s - with no filtering.
      
      - e.g. `falcon_multiqc query --tool-metric verifybamid AVG_DP '<' 28 -o path`

      - e.g. `falcon_multiqc query --tool-metric verifybamid AVG_DP 0 0 -o path` will give all verifybamid AVG_DP in output


    - Special characters must be escaped (wrapped in single quotes) in bash, like '<'.

- Specify output path with `--output or -o`. 
- Specify output filename with `--filename` or `-f` (required if using output/csv/multiqc).
- Specify output type with either `--csv` or `--multiqc`.
   - Default output is stdout.

#### 4. Chart
This command allows you to visualise the output of the `query` command. The output will be a html file (path and name specified by `--output`), with each value hoverable for extra details. 

- Input should be a csv from `query` command: supports stdin or `--data path/to/query_output.csv`

- `--output` specifies where to save the output (include filename).
- `--type` [histogram / box / bar] type of chart.
- `--compare` x-axis of box and bar, overlapped group on histogram. **Required for bar**. Must be a column header of the query output e.g. `raw_data.PCT_EXC_DUPE` or `batch.description`
- ##### Histogram (use for metrics summary [vs groups])
  - `--compare` column that will be plotted overlapping on the same histogram [Optional].
  - Supports 1 metric only. If multiple present, will only use the first.
- ##### Bar (use for metrics vs categorical data)
  - `--compare` column that will be plotted on the x-axis **categorically** (not numerically) [Required].
  - Supports multiple metrics (will be plotted as separate graphs).
- ##### Box (use for metrics [vs groups])
  - `--compare` column that will be plotted on the x-axis [Optional].
  - Supports multiple metrics (will be plotted as separate graphs).


#### 5. SQL
This command allows you to query the falcon multiqc database using raw SQL.

NOTE: example_1, example_2, example_3 can be found in the sql.py doc string.
Options:

- `--sql <path.txt>` Enter path (relative or absolute) to .txt containing raw SQL statement
    See example_1, example_2, example_3 for examples

- `--output <path>` Specify the directory to save either your csv or multiqc result when using the `--csv` or `--multiqc` options

- `--filename <filename>` Name (no extensions) the csv or multiqc html report when using the `--csv` or `--multiqc` options

- `--csv` Creates csv file in output directory from query result 
    See example_2

- `--multiqc` Use this flag to generate a multiqc report from query, saved in output directory. 
    See example_3
    NOTE: To use, you must make sure to select for 'sample.sample_name' AND 'batch.path'
          Do not specify an alias, just do: SELECT sample.sample_name, batch.path
    NOTE: To select for 'sample.sample_name' AND 'batch.path' you must join batch table with sample table

- `--overview` Prints an overview of the number of samples in each batch/cohort.

NOTE: If `--multiqc` or `--csv` flags are not used, result will print to stdout.
    See example_1

#### 6. Check Database
This command allows you to checks the paths in your database are still valid and and fix invalid paths.

- Use `falcon_multiqc check_db --help` to see how to use the check database command.
- E.g. `falcon_multiqc check_db`
- Optional parameter `--skip-update` skips prompts for invalid paths while checking the database.

#### 7. Remove
Command for removing entries from database.

`--overview` Prints an overview of the number of samples in each batch/cohort.
`--cohort <cohortID>` - removes all entries associated with that cohort throughout database.
`--batch <cohortID Batch_name>` - removes all entries associated with that batch throughout database.

NOTE: although you can use multiple --batch or --cohort options in one command, if both are used together, only --cohort will commit.

=====================================================================================================================================

## Dev instructions
1. `git clone https://github.com/lwratten/project-falcon.git`
2. `cd project-falcon`
3.  Ensure your system has the tools in requirements.system installed.
4. `python3 -m venv env` create a python virtual environment if you haven't already
5. `source env/bin/activate`  activate / go into the virtual environment
6. `pip install --editable .` this allows you to install the tool and updates automatically if you edit it (re-install if you change any of the cli / click things)
