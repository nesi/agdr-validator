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