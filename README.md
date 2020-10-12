# project-falcon
A tool for parsing multiqc reports into a database and querying from the command-line


## dev instructions
1. `git clone https://github.com/lwratten/project-falcon.git`
2. `cd project-falcon`
3. `python3 -m venv env` create a python virtual environment if you haven't already
4. `source env/bin/activate`  activate / go into the virtual environment
5. `pip install --editable .` 


### Files
* Directory `falcon_multiqc` contains the core code of the tool.
* Directory `commands` contains Click commands, e.g. save. 
* File `falcon_multiqc/cli.py` sets up Click so it will automatically search the `commands` directory for commands. After installing, run `falcon_multiqc` and see the commands available.
* File `setup.py` allows you to use `pip install --editable .` or `pip install .`.


## user instructions
1. The above dev instructions + `falcon_multiqc` command.