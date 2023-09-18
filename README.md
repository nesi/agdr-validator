## Quickstart

The first version has limited functionality. 
Please check `README.md` for information on new features as 
they are added.

### Clone repository

```
# ssh
git clone git@git.hpcf.nesi.org.nz:gen3/validator.git

# https
git clone https://git.hpcf.nesi.org.nz/gen3/validator.git
```

### (optional) Create virtual environment

`python3 -m venv venv`

### (optional) Activate virtual environment

`source venv/bin/activate`

### Upgrade pip

`pip install --upgrade pip`

### Install module

`pip install -e .`

### Run validator on input spreadsheet

`agdrvalidator -s test/data/AGDR_Metadata_Venenivibrio.xlsx`

- output will be appended to `report.txt` by default
- you may specify a desired output filename

```
agdrvalidator -h
usage: agdrvalidator [-h] -s SPREADSHEET [-o OUTPUT]

Generate validation report for AGDR metadata ingest

options:
  -h, --help            show this help message and exit
  -s SPREADSHEET, --spreadsheet SPREADSHEET
                        path to excel input file containing metadata
  -o OUTPUT, --output OUTPUT
                        path to output file for validation report
```

### Example Outputs

Happy path, no errors in the spreadsheet:
```(venv) eirian> agdrvalidator -s demo/AGDR_Metadata_Venenivibrio.xlsx
(venv) eirian> cat report.txt
project 	... OK!
experiment 	... OK!
organism 	... OK!
environmental 	... OK!
file 	... OK!
read_group 	... OK!
```

Sad path, error discovered in the spreadsheet (with description of error):
```
(venv) eirian> rm report.txt
(venv) eirian> agdrvalidator -s demo/AGDR_Metadata_Venenivibrio.xlsx
(venv) eirian> cat report.txt
project 	... OK!
experiment 	... OK!
organism 	... OK!
environmental 	... INVALID!
	submitter_id:	Duplicate submitter_id: AP

file 	... OK!
read_group 	... OK!
```

The expected output format is subject to change, and the `README.md` will 
be updated accordingly.