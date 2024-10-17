'''
@Author: Eirian Perkins

This file provides the main entry point for the package. 
It provides a command line interface for the package using the argparse module.
'''

import agdrvalidator.globals.loglevel as logsettings
import agdrvalidator.globals.version as version

import os
import shutil
import argparse
import datetime
import logging


def getParser():
    parser = argparse.ArgumentParser(prog="agdrvalidator",
                                     description="Generate validation report for AGDR metadata spreadsheet and/or TSV files for metadata ingest")
    #parser.add_argument("-d", "--dictionary", help="path to dictionary file", required=False)
    parser.add_argument("-s", "--spreadsheet", help="path to excel input file containing metadata", required=True)
    parser.add_argument("-o", "--stdout", help="write validation report to stdout, otherwise a filename will be generated based on the project code and date of report generation", required=False, action='store_true')
    parser.add_argument("-p", "--project", help="Project code, e.g. AGDRXXXXX, required for TSV output. If unspecified, project code will default to AGDR99999.", required=False)
    parser.add_argument("-r", "--program", help="Program name, required for TSV output. If unspecified, program name will default to TAONGA", required=False)
    parser.add_argument("-t", "--tsv", help="include this flag to convert spreadsheet to TSV output for Gen3 ingest", required=False, action='store_true')
    parser.add_argument("-l", "--loglevel", type=int, help="verbosity level, for debugging. Default is 0, highest is 3", required=False)
    parser.add_argument('-v', '--validate', action='count', default=0, help="validate the input file. -v will generate a report with all detected errors; -vv will generate a report with all detected errors and warnings. Default is 0.")
    parser.add_argument("--version", action="version", version=version.version("0"))
    return parser


def cleanUpFile(filename):
    '''
    if a validation report of the same name already exists, remove it

    this is a hacky way to implement overwrite
    '''
    if not filename:
        return
    try:
        os.remove(filename)
    except OSError:
        pass

def cleanUpDir(dirpath):
    '''
    if TSV output for the indicated project already exists, remove it

    this is a hacky way to implement overwrite
    '''
    if not dirpath:
        return
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)

def main():
    parser = getParser()

    args = parser.parse_args()
    project = args.project
    if not project:
        project = "AGDR99999"
    program = args.program
    verbosity = args.loglevel
    if verbosity:
        if verbosity <= 0:
            logsettings.init(level=logging.ERROR)
        elif verbosity == 1:
            logsettings.init(level=logging.WARN)
        elif verbosity == 2:
            logsettings.init(level=logging.INFO)
        elif verbosity >= 3:
            logsettings.init(level=logging.DEBUG)
    else:
        logsettings.init(level=logging.ERROR)
    validation_verbosity = args.validate
    write_to_stdout = args.stdout

    #from agdrvalidator.parser.excel.agdrspreadsheet import Agdr as Agdr
    from agdrvalidator.parser.excel.agdrspreadsheet_2024_08_28 import Agdr as AgdrSpreadsheetParser
    from agdrvalidator.schema.agdrschema_2024_09_10 import AGDR as AGDRSchema
    from agdrvalidator.data.dictionaries.agdrdictionary_2024_09_10 import loadDictionary
    from agdrvalidator.schema.validator_2024_09_10 import AGDRValidator as AGDRValidator


    excelpath = args.spreadsheet
    metadata = AgdrSpreadsheetParser(excelpath)
    print(f"VALIDATOR VERSION: \t\t{version.version(metadata.version)}\n")
    metadata.parse()

    schema = loadDictionary()

    # is clearly a dictionary
    #print(f"from main: metadata.nodes: {metadata.nodes}")
    # print type of metadata.nodes:
    #print(f"type of metadata.nodes: {type(metadata.nodes)}")
    agdrschema = AGDRSchema(schema, metadata.nodes, project=project, program=program)

    report_file = None 
    if not write_to_stdout:
        report_file = f"{project}_Validation_Report_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt"
    cleanUpFile(report_file)
    validator = AGDRValidator(schema, agdrschema, report_file)
    validator.validate(validation_verbosity)

    if args.tsv:
        print("\nGENERATING TSV FILES...")
        if not project:
            project = "AGDR99999"
        directory = f"{project}_TSV_Output_{datetime.datetime.now().strftime('%Y-%m-%d')}"
        cleanUpDir(directory)
        print(f"\tDIRECTORY:\t{directory}")
        agdrschema.toTSV(directory)


if __name__ == "__main__":
    main()