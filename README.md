## Quickstart

The first version has limited functionality. 
Please check `README.md` for information on new features as 
they are added.

WARNING: A minimum version of Python 3.7 is assumed.

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

`agdrvalidator -s test/data/AGDR_Metadata_Venenivibrio.xlsx`

- output will be appended to `AGDR99999_validation_report_YYYY-MM-DD.txt` by default with YYYY-MM-DD being the date when the output was created
- you may specify a desired output filename with -o
- the version of the validator is displayed. Any issue with the validator, please report the version number

example2: 
`agdrvalidator -t -p AGDR00051 -s test/data/AGDR_Metadata_Venenivibrio.xlsx`
- as well as being validated, TSV files will be created for the program TAONGA and project AGDR00051

```
agdrvalidator -h
usage: agdrvalidator [-h] -s SPREADSHEET [-o OUTPUT] [-p PROJECT] [-t]

Generate validation report for AGDR metadata ingest

options:
  -h, --help            show this help message and exit
  -s SPREADSHEET, --spreadsheet SPREADSHEET
                        path to excel input file containing metadata
  -o OUTPUT, --output OUTPUT
                        path to output file for validation report
  -p PROJECT, --project PROJECT
                        Project code, e.g. AGDRXXXXX, required for TSV output
  -r PROGRAM, --program PROGRAM
                        Program name, required for TSV output. If unspecified, program name will default to TAONGA
  -t, --tsv             include this flag to convert spreadsheet to TSV output for
                        Gen3 ingest
  -v, --version         show program's version number and exit
```

#### Version Number of the Validator
M.m.dictv example 1.0.20220923
with M the Major version, m the minor version and dictv the version of the dictionary.


#### Example Outputs

Happy path, no errors in the spreadsheet:
```(venv) eirian> agdrvalidator -s test/data/AGDR_Metadata_Venenivibrio.xlsx
(venv) eirian> cat AGDR99999_validation_report_YYYY-MM-DD.txt
project: AGDR99999 	... OK!
experiment: NZ_GEOTHERMAL_METAGENOMES_01 	... OK!
experiment: NZ_GEOTHERMAL_MAGS_01 	... OK!
environmental: AP 	... OK!
environmental: CPc 	... OK!
environmental: CPp 	... OK!
environmental: CPr 	... OK!
environmental: IMP.14_MG 	... OK!
environmental: IMP.15_MG 	... OK!
environmental: P1.0037_MG 	... OK!
environmental: P1.0103_MG 	... OK!
raw: AGDR99999_RAW_0 	... OK!
raw: AGDR99999_RAW_1 	... OK!
processed_file: AGDR99999_PROCESSED_FILE_0 	... OK!
processed_file: AGDR99999_PROCESSED_FILE_1 	... OK!
processed_file: AGDR99999_PROCESSED_FILE_2 	... OK!
processed_file: AGDR99999_PROCESSED_FILE_3 	... OK!
read_group: AGDR99999_READ_GROUP_0 	... OK!
read_group: AGDR99999_READ_GROUP_1 	... OK!
```

Sad path, error discovered in the spreadsheet (with description of error):
```
(venv) eirian> rm AGDR99999_validation_report_YYYY-MM-DD.txt
(venv) eirian> agdrvalidator -s test/data/AGDR_Metadata_Venenivibrio.xlsx
(venv) eirian> cat AGDR99999_validation_report_YYYY-MM-DD.txt
project: AGDR99999 	... OK!
experiment: NZ_GEOTHERMAL_METAGENOMES_01 	... OK!
experiment: NZ_GEOTHERMAL_MAGS_01 	... OK!
environmental: AP 	... OK!
environmental: AP  	... INVALID!
	submitter_id:	Duplicate submitter_id: AP
environmental: CPp 	... OK!
environmental: CPr 	... OK!
environmental: IMP.14_MG 	... OK!
environmental: IMP.15_MG 	... OK!
environmental: P1.0037_MG 	... OK!
environmental: P1.0103_MG 	... OK!
raw: AGDR99999_RAW_0 	... OK!
raw: AGDR99999_RAW_1 	... OK!
processed_file: AGDR99999_PROCESSED_FILE_0 	... OK!
processed_file: AGDR99999_PROCESSED_FILE_1 	... OK!
processed_file: AGDR99999_PROCESSED_FILE_2 	... OK!
processed_file: AGDR99999_PROCESSED_FILE_3 	... OK!
read_group: AGDR99999_READ_GROUP_0 	... OK!
read_group: AGDR99999_READ_GROUP_1 	... OK!
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
