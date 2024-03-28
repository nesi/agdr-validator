## Quickstart

The first version has limited functionality. 
Please check `README.md` for information on new features as 
they are added.

**WARNING**: A minimum version of Python 3.7 is assumed.

### Clone repository

```
# ssh
git clone git@git.hpcf.nesi.org.nz:gen3/validator.git

# https
git clone https://git.hpcf.nesi.org.nz/gen3/validator.git
```

### (recommended) Create virtual environment

`python3 -m venv venv`

### (recommended) Activate virtual environment

`source venv/bin/activate`
Note: to deactivate the env, just type `deactivate`

### Upgrade pip

`pip install --upgrade pip`

### Install module

`pip install -e .`

### Run validator on input spreadsheet
example1: 

`agdrvalidator -s test/data/AGDR_Metadata_Venenivibrio.xlsx -v -p AGDR99999`

- the `-v` option is required in order to perform validation, or else validation is skipped
  - using `-vv` will increase **validation** verbosity. By default, only errors are displayed. `-vv` will also display warnings and informational messages, for instance if optional links between nodes are not set.
  - the report will be written to a file based on the project code and the current date. Use the `--stdout` flag to display the validation report in the terminal instead.
- output will be appended to `AGDR99999_validation_report_YYYY-MM-DD.txt` by default with YYYY-MM-DD being the date when the output was created, and `AGDR99999` being the project code specified by the `-p` flag. This should always be specified when doing TSV generation as it specifies the project the metadata is associated with.
- flags may be specified in any order
- the version of the validator will always be displayed. Any issue with the validator, please report the version number. If `--version` is specified, the validator will display the version number and exit.

example2: 
`agdrvalidator -t -p AGDR00051 -s test/data/AGDR_Metadata_Venenivibrio.xlsx -v`
- as well as being validated, TSV files will be created for the program TAONGA and project AGDR00051

```
$ agdrvalidator --help
usage: agdrvalidator [-h] -s SPREADSHEET [-o] [-p PROJECT] [-r PROGRAM] [-t] [-l LOGLEVEL] [-v] [--version]

Generate validation report for AGDR metadata spreadsheet and/or TSV files for metadata ingest

options:
  -h, --help            show this help message and exit
  -s SPREADSHEET, --spreadsheet SPREADSHEET
                        path to excel input file containing metadata
  -o, --stdout          write validation report to stdout, otherwise a filename will be generated based on the project code and date of report generation
  -p PROJECT, --project PROJECT
                        Project code, e.g. AGDRXXXXX, required for TSV output. If unspecified, project code will default to AGDR99999.
  -r PROGRAM, --program PROGRAM
                        Program name, required for TSV output. If unspecified, program name will default to TAONGA
  -t, --tsv             include this flag to convert spreadsheet to TSV output for Gen3 ingest
  -l LOGLEVEL, --loglevel LOGLEVEL
                        verbosity level, for debugging. Default is 0, highest is 3
  -v, --validate        validate the input file. -v will generate a report with all detected errors; -vv will generate a report with all detected errors and warnings. Default is 0.
  --version             show program's version number and exit
```

#### Version Number of the Validator
M.m.dictv example 1.0.20220923
with M the Major version, m the minor version and dictv the version of the dictionary.


#### Example Outputs

Happy path, no errors in the spreadsheet (note that `-o` pipes the validation 
report to stdout):
```
(venv) eirian> agdrvalidator -s TestValues2.xlsx -v -o
VALIDATOR VERSION: 		1.2.20220923

	Parsing AGDR spreadsheet |███| 3 in 0.1s (17.15/s)
	Loading data dictionary  |████████████████████████████████████████| 54 in 0.0s (9158.23/s)
	Building metadata graph  |████████████████████████████████████████| 100% in 0.2s (12.72%/s)
PERFORMING VALIDATION...
on 12: 	NO ERRORS DETECTED
	Validating schema        |████████████████████████████████████████| 12/12 [100%] in 0.0s (352.84/s)
...VALIDATION COMPLETE
```
Please provide feedback to the development team if you would like any 
changes to the output format.

Sad path, error discovered (duplicate `submitter_id` in Environmental field from the spreadsheet). The 
`agdrvalidator` constructs placeholder nodes that aren't explicitly included in the spreadsheet,
which is why the error message refers to `metagenome`, `sample`, and `aliquot` nodes even though the 
spreadsheet error is in the `Environmental` field. 
```
(venv) eirian> cat AGDR99999_Validation_Report_2024-03-28.txt
METAGENOME
	ERROR: duplicate submitter_id found for metagenome node: CPc
	ERROR: duplicate submitter_id found for metagenome node: CPc
SAMPLE
	ERROR: duplicate submitter_id found for sample node: CPc_SAMPLE
	ERROR: duplicate submitter_id found for sample node: CPc_SAMPLE
ALIQUOT
	ERROR: duplicate submitter_id found for aliquot node: CPc_ALQ
	ERROR: duplicate submitter_id found for aliquot node: CPc_ALQ
READ_GROUP
	ERROR:	no REQUIRED link found connecting parent [aliquot] link to child [read_group:AP_RG_R1]
read_group [AP_RG_R1]
	barcoding_applied
		Expected a boolean value, but received [Unknown] instead
	includes_spike_ins
		Expected a boolean value, but received [Unknown] instead
	read_length
		Expected an integer value, but received [Unknown] instead
	to_trim_adapter_sequence
		Expected a boolean value, but received [Unknown] instead
```

The expected output format is subject to change, and the `README.md` will 
be updated accordingly.


#### Generating TSV output

The validator can also generate a TSV file used for metadata ingest 
into the AGDR. TSV generation occurs regardless of whether validation is 
successful, so it is important to check the validation report for errors.

Supply the `-t` flag on the commandline to enable TSV generation.

`submitter_id` generation rules are as follows:

- core_metadata_collection: `project_code` + `_CMC01` 
- experiment: supplied by user via metadata spreadsheet 
- sample: `sample_id` + `_SAMPLE`
- aliquot: `sample_id` + `_ALQ`
- publication: `sample_id` + `_PUB`
- raw: filename 
- processed_file: filename


#### When things go wrong

If you are using the validator and encounter an error or unexpected behaviour,
it would be most helpful if you could re-run the command with the 
`-l 3` option. This will generate a log file with the highest verbosity 
level, which will help developers to diagnose the issue.
