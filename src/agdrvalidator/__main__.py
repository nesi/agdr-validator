import agdrvalidator.utils.investigation as ivst
import agdrvalidator.schema.investigation as divst
from agdrvalidator.parser.dictionary.gen3parser import Gen3 as Gen3Dictionary
from agdrvalidator.parser.excel.agdrspreadsheet import *
from agdrvalidator.schema.agdrschema_2022_09_23 import AGDR as AGDRSchema
from agdrvalidator.data.dictionaries.agdrdictionary_2022_09_23 import loadDictionary
import os
import argparse
import datetime

DATADIR = "test/data"
DICTIONARY = "gen3.nesi_2022_09_23.json"

def testmain():
    #print(ivst.book)
    #print(dir(ivst.pdbook))
    #for item in dir(ivst.pdbook):
    #    print(item)
    #print(ivst.pdbook[1])

    # ok, works
    #pr = ivst.PrototypeReader()
    #pr.readBook(os.path.join(ivst.DATADIR, ivst.VENENIVIBRIO))
    #pr.viewBook()

    # next investigate parsing dictionary
    #pdr = divst.PrototypeDictionaryReader()
    #pdr.readDictionary(os.path.join(divst.DATADIR, divst.DICTIONARY))

    VENENIVIBRIO = "AGDR_Metadata_Venenivibrio.xlsx"

    d = os.path.join(DATADIR, DICTIONARY)
    print("dictionary: ", d)
    g3d = Gen3Dictionary(d)
    g3d.parse()
    #g3d.pprint()

    # TODO
    # first pass through: apply pattern to all properties
    excel = os.path.join(DATADIR, VENENIVIBRIO)
    agdr = Agdr(excel)
    agdr.parse()

def getParser():
    parser = argparse.ArgumentParser(prog="agdrvalidator",
                                     description="Generate validation report for AGDR metadata ingest")
    #parser.add_argument("-d", "--dictionary", help="path to dictionary file", required=False)
    parser.add_argument("-s", "--spreadsheet", help="path to excel input file containing metadata", required=True)
    parser.add_argument("-o", "--output", help="path to output file for validation report", required=False)
    parser.add_argument("-p", "--project", help="Project code, e.g. AGDRXXXXX, required for TSV output. If unspecified, project code will default to AGDR99999.", required=False)
    parser.add_argument("-r", "--program", help="Program name, required for TSV output. If unspecified, program name will default to TAONGA", required=False)
    parser.add_argument("-t", "--tsv", help="include this flag to convert spreadsheet to TSV output for Gen3 ingest", required=False, action='store_true')
    return parser

def main():
    parser = getParser()

    args = parser.parse_args()
    output = args.output
    project = args.project
    program = args.program

    excel = args.spreadsheet
    agdr = Agdr(excel)
    agdr.parse()

    schema = loadDictionary()

    validator = AGDRSchema(schema, agdr, report=output, project=project, program=program)
    validator.validate()

    if args.tsv:
        print("\n\nConverting to TSV...")
        validator.toTSV(f"{project}_TSV_Output_{datetime.datetime.now().strftime('%Y-%m-%d')}")



if __name__ == "__main__":
    main()