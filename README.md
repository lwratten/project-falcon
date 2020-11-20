# falcon-multiqc
A tool for parsing multiqc reports into a database with querying and charting capabilities from the command-line

## User Setup
1. Clone the repository to your local machine using `git clone https://github.com/lwratten/project-falcon.git`.
2. Navigate to the repository using `cd project-falcon`.
3. Ensure your system has the tools in `requirements.system` installed.
4. Use `python3 -m venv env` to create a python virtual environment if you haven't already.
5. Use `source env/bin/activate` to go into the virtual environment.
6. Install software requirements using `pip install --editable .`

### System Requirements
Falcon MultiQC supports Linux based operating systems with the system requirements required to install the tool (as described in requirements.system).

### Database Server Setup
Falcon MultiQC requires a PostgreSQL database server to have already been set up. Keep note of your server’s username, password and port. This information is required when connecting FalconMultiQC to your server.
<br>
## Commands
- Use `falcon_multiqc --help` to see a list of commands and what they do. Each of the following commands also has a help page accessible via `falcon_multiqc <command> --help`.
<br>
#### Connect 


```
falcon_multiqc connect
```

This command connects the user to a postgres database and creates a new database if one doesn't exist.

- Use `falcon_multiqc connect --help` to see how to use the connect command.
- E.g. `falcon_multiqc connect` will prompt you to enter your username and password and connect to the database.
- Optional Parameters:
  - `--uri` <Database URI> -- Enter a URI to connect to the database with (URI in the form `postgres+psycopg2://USERNAME:PASSWORD@IP_ADDRESS:PORT/DATABASE_NAME`).
  - `--skip-check` -- Skip checking file paths in the database when connecting to an existing database


```
falcon_multiqc save
```


This command saves multiqc data to the database. You can save one directory at a time using `--directory` or multiple using the `--input_csv` option. One of these two input options are required.

##### Saving one directory:



###### Required Parameters:

*   `--directory` Path to the multiqc output directory to be saved
*   `--sample_metadata` Path to the sample metadata file (see sample_metadata below)  \



###### Optional Parameters:

*   `--batch_description` String of a description to give every batch in this input.
*   `--cohort_description` String of a description to give every cohort in this input.
*   `--batch_metadata `Path to file with batch_metadata (see batch_metadata below)
*   `--cohort_metadata` Path to file with cohort_metadata (see cohort_metadata below)

<br>
##### Saving multiple directories (bulk saving):

###### Required Parameters:

*   `--input_csv` Path to the input csv of paths and metadata paths (see input_csv) \

    *   If using this option, directory and sample_metadata parameters are not required.

<br>
##### sample_metadata (required):

A CSV (comma-separated) in the format with the following format…


<table>
  <tr>
   <td>Sample Name
   </td>
   <td>Cohort Name 
   </td>
   <td>Batch Name
   </td>
   <td>Flowcell.Lane
   </td>
   <td>Library ID
   </td>
   <td>Platform
   </td>
   <td>Centre of Sequencing
   </td>
   <td>Reference Genome
   </td>
   <td>Type 
   </td>
   <td>Description
   </td>
  </tr>
</table>


<br>
##### batch_metdata (optional):

A CSV (comma-separated) in the format with the following format…


<table>
  <tr>
   <td>Batch Name
   </td>
   <td>Number of Samples
   </td>
   <td>Description
   </td>
  </tr>
</table>


`--batch_metadata` can also be used on its own to save batch metadata to a batch that already exists in the database.
<br>

##### cohort_metadata (optional):


<table>
  <tr>
   <td>Cohort Name
   </td>
   <td>Number of Samples
   </td>
   <td>Number of Batches
   </td>
   <td>Description
   </td>
  </tr>
</table>


`--cohort_metadata` can also be used on its own to save cohort metadata to a cohort that already exists in the database.

<br>
##### Save Examples:


<table>
  <tr>
   <td><strong>Saving one directory</strong>
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc save -d project/project_falcon/data/  -s project/project_falcon/data/MGRBSampleMetadata.csv </code>
   </td>
  </tr>
</table>



<table>
  <tr>
   <td><strong>Saving multiple directories (bulk saving)</strong>
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc save -i project/project_falcon/data/input.csv</code>
<p>
<code>Where input.csv contains:</code>
<p>
<code>directory, sample_metadata</code>
<p>
<code>project/data/batch1, project/data/batch1_metadata.csv</code>
<p>
<code>project/data/batch2, project/data/batch2_metadata.csv</code>
<p>
<code>project/data/batch3, project/data/batch3_metadata.csv</code>
   </td>
  </tr>
</table>



<table>
  <tr>
   <td><strong>Saving batch_metadata descriptions</strong>
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc save -bm d/project/project_falcon/data/Cohort2BatchData.csv </code>
   </td>
  </tr>
</table>

<br>
#### Query
```
falcon_multiqc query
```
This command allows you to query the falcon multiqc database. All parameters are optional to query. Adding multiple options for --select or any of the filters is supported.
##### 1. Select:

`--select` table information that will be included in the output. 

*   Either ‘sample [default]’, ‘batch’, ‘cohort’ or ‘tool-metric’. 
*   The entire table’s columns will be included in the output if selected.
*   Selecting ‘tool-metric’ will result in the metric/s as its own column in the output.

##### Query Select Examples:


<table>
  <tr>
   <td><strong>Output all batch and sample columns</strong>
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc query --select batch --select sample</code>
   </td>
  </tr>
</table>

##### 2. Filtering:

Add filtering with the following options. Multiple filters will behave like OR. Multiple `--tool-metric`s behave like AND.

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
    
**Extra Notes on Using `--tool-metric`** **Filter:**
*   Special characters must be escaped (wrapped in single quotes) in bash, like '&lt;'.
*   You must always specify 4 values with `--tool-metric &lt;tool name> &lt;metric> &lt;operator> &lt;value>`.
*   The `&lt;operator> ` has to be one of **<code>'>', '>=','&lt;','&lt;=','==','!='</code></strong>
*   If you only want to filter by <code>&lt;tool name></code> and <code>&lt;metric></code> (not operator / value) and therefore get results with that metric regardless of its value… give dummy invalid values to the 3rd and 4th argument.  \

    *   E.g.<code> --tool-metric &lt;tool name> &lt;metric> 0 0</code> invalid &lt;operator> values indicate to the program to ignore them.

##### Query Filter Examples:


<table>
  <tr>
   <td><strong>Filter by multiple batches</strong>
<p>
This will result in all samples (default --select sample) with a batch.id of ‘AAA’ or ‘AAB’.
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc query --batch AAA --batch AAB</code>
   </td>
  </tr>
</table>



<table>
  <tr>
   <td><strong>Filter by tool-metric</strong>
<p>
This will result in all samples with the tool ‘verifybamid’ and metric ‘AVG_DP’ with a value of less than 30.
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc query --tool-metric 'verifybamid' 'AVG_DP' '&lt;' '30'</code>
   </td>
  </tr>
</table>



<table>
  <tr>
   <td><strong>Filter by tool-metric (string)</strong>
<p>
This will result in all samples with the tool ‘picard_gcbias’ and metric ‘READS_USED’ with a value of ‘ALL’.
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc query --tool-metric 'picard_gcbias' 'READS_USED' '==' 'ALL'</code>
   </td>
  </tr>
</table>



<table>
  <tr>
   <td><strong>Output all tool-metric values</strong>
<p>
This will result in all samples with the tool ‘verifybamid’ and metric ‘AVG_DP’.
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc query --tool-metric 'verifybamid' 'AVG_DP' 0 0</code>
   </td>
  </tr>
</table>



<table>
  <tr>
   <td><strong>Filter by multiple tool-metric</strong>
<p>
This will result in all samples with a MEAN_INSERT size greater than 420 AND PCT_EXC_DUPE less than or equal to 0.021 AND an AVG_DP less than 30 AND number of reads less than 2469490, including an output column for each metric (see <code>--select tool-metric</code>)
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc query \</code>
<p>
<code>--select sample</code>
<p>
<code>--select tool-metric</code>
<p>
<code>--tool-metric picard_insertSize MEAN_INSERT_SIZE '>' 420 \</code>
<p>
<code>--tool-metric picard_wgsmetrics PCT_EXC_DUPE '&lt;=' 0.0921 \</code>
<p>
<code>--tool-metric verifybamid AVG_DP '&lt;' 30 \</code>
<p>
<code>--tool-metric verifybamid '#READS' '&lt;' 2469490</code>
   </td>
  </tr>
</table>

##### Query Output Examples: 

<table>
  <tr>
   <td><strong>Output query as a csv</strong>
   </td>
  </tr>
  <tr>
   <td><code>falcon_multiqc query \</code>
<p>
<code>--tool-metric picard_insertSize MEAN_INSERT_SIZE '>' 420 \</code>
<p>
<code>--select tool-metric \</code>
<p>
<code>--select sample \</code>
<p>
<code>--csv \</code>
<p>
<code>--output output \</code>
<p>
<code>--filename mean_insert_size \</code>
   </td>
  </tr>
</table>

<br>

#### Chart

```
falcon_multiqc chart
```

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

<br>
#### SQL
This command allows you to query the falcon multiqc database using raw SQL.

NOTE: example_1, example_2, example_3 can be found in the sql.py doc string.
Options:

- `--sql <path.txt>` Enter path (relative or absolute) to .txt containing raw SQL statement
    See example_1, example_2, example_3 for examples

- `--output <path>` Specify the directory to save either your csv or multiqc result when using the `--csv` or `--multiqc` options

- `--filename <filename>` Name (no extensions) the csv or multiqc html report when using the `--csv` or `--multiqc` options

- `--csv` Creates csv file in output directory from query result 
    See example_2, example_3

- `--multiqc` Use this flag to generate a multiqc report from query, saved in output directory. 
    See example_3
    NOTE: To use, you must make sure to select for 'sample.sample_name' AND 'batch.path'
          Do not specify an alias, just do: SELECT sample.sample_name, batch.path
    NOTE: To select for 'sample.sample_name' AND 'batch.path' you must join batch table with sample table

- `--overview` Prints an overview of the number of samples in each batch/cohort.

NOTE: If `--multiqc` or `--csv` flags are not used, result will print to stdout.
    See example_1
<br>
#### Check Database

```
falcon_multiqc check_db
```


Command that checks that all paths saved within the database are still valid. Prompts the user to fix invalid paths.

Optional Parameter:



*   `--skip-update` skips prompts for invalid paths while checking the database.
<br>

#### Remove
```
falcon_multiqc remove
```
Command for removing entries from database.

`--overview` Prints an overview of the number of samples in each batch/cohort.
`--cohort <cohortID>` - removes all entries associated with that cohort throughout database, can be used multiple times.
`--batch <cohortID Batch_name>` - removes all entries associated with that batch throughout database, can be used multiple times.

NOTE: Don't use --batch or --cohort options in one command, use two seperate commands instead.


## Database Column Names {#database-column-names}

The following information may be useful for using the `--compare` option in the chart command.


<table>
  <tr>
   <td><strong>Sample Table</strong>
   </td>
   <td><strong>Batch Table</strong>
   </td>
   <td><strong>Cohort Table</strong>
   </td>
  </tr>
  <tr>
   <td>sample.id (unique)
   </td>
   <td>batch.id (unique)
   </td>
   <td>Cohort.id (unique and user provided)
   </td>
  </tr>
  <tr>
   <td>sample.sample_name (user provided)
   </td>
   <td>batch.batch_name (user provided)
   </td>
   <td>cohort.sample_cohort
   </td>
  </tr>
  <tr>
   <td>sample.flowcell_lane
   </td>
   <td>batch.path
   </td>
   <td>cohort.batch_count
   </td>
  </tr>
  <tr>
   <td>sample.library_id
   </td>
   <td>batch.sample_count
   </td>
   <td>cohort.description
   </td>
  </tr>
  <tr>
   <td>sample.platform
   </td>
   <td>batch.description
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>sample.centre
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>sample.reference_genome
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>sample.type
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>sample.description
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
</table>


**RawData Table:** tool-metric is named raw_data.metric in query output.

