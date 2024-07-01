from agdrvalidator.parser.excel.agdrspreadsheet import *
from agdrvalidator.parser.dictionary.gen3parser import Gen3 as Gen3Dictionary
from agdrvalidator.schema.agdrschema_2024_03_25 import AGDR as AGDRSchema
#from agdrvalidator.schema.gen3schema import Gen3 as Gen3Schema

#import pandas as pd
#import pytest
#import random
#import string
#import tempfile
import os

DATADIR = "test/data"
DICTIONARY = "gen3.nesi_2024_03_25.json"
VENENIVIBRIO = "AGDR_Metadata_Venenivibrio.xlsx"
VENENIVIBRIO_VALID = "AGDR_Metadata_Venenivibrio CORRECTED.xlsx"

def test_pattern_application_foo():
    # read in metadata from researcher
    excel = os.path.join(DATADIR, VENENIVIBRIO)
    rs_data = Agdr(excel)
    rs_data.parse()

    # read in dictionary (metadata structure)
    d = os.path.join(DATADIR, DICTIONARY)
    print("dictionary: ", d)
    g3dict = Gen3Dictionary(d)
    schema = g3dict.parse()
    #g3d.pprint()

    # first pass through: apply pattern to all properties
    
    # I want some Validate class, it takes everything from the dictionary 
    # and applies the read-in gen3 structure to it 

    # so, let's have a look, let's say I want to validate a single property
    # for all data of a particular node
    # example, check that
    #       Metagenome has latitude_decimal_degrees parsable as a number or null 
    #              <- requires several levels of indirection, tests parsing robustness
    #       Experiments have all required properties

    #print(rs_data.Project.required)
    print("\t".join([str(x) for x in rs_data.Project.required[0]]))
    print("-------")
    #print("\t".join(rs_data.Project.header[0]))
    print("\t".join([str(x) for x in rs_data.Project.header[0]]))
    print("-------")
    for row in rs_data.Project.data:
        print("\t".join([str(x) for x in row]))
        print()

    print("--------------------")
    print("--------------------")
    print("investigator name:")
    print(rs_data.Project.get("investigator_name"))

    # now do example of getting Project out of dictionary
    #for prop in schema.nodes["project"]._properties:
    #for prop in schema.nodes["experiment"]._properties:
    #for prop in schema.nodes["organism"]._properties:
    #for prop in schema.nodes["metagenome"]._properties:
    #for prop in schema.nodes["processed_file"]._properties:

    print("Walking the schema.....")
    print("---")
    #schema.walk(True)
    for node in schema.walk(True):
        print(node.name)
    print()
    print("Walking the schema WITHOUT revisiting nodes.....")
    print("---")
    #schema.walk(False)
    for node in schema.walk(False):
        print(node.name)


    print(".................................")
    validator = AGDRSchema(schema, rs_data)
    #print(validator._nodes.keys())
    #validator._nodes["project"].validate()
    validator.validate()

def test_pattern_application_foo():
    # read in metadata from researcher
    excel = os.path.join(DATADIR, VENENIVIBRIO)
    rs_data = Agdr(excel)
    rs_data.parse()

    # read in dictionary (metadata structure)
    d = os.path.join(DATADIR, DICTIONARY)
    g3dict = Gen3Dictionary(d)
    schema = g3dict.parse()

    validator = AGDRSchema(schema, rs_data)
    validator.validate()

def test_pattern_application_foo_valid():
    # read in metadata from researcher
    excel = os.path.join(DATADIR, VENENIVIBRIO_VALID)
    rs_data = Agdr(excel)
    rs_data.parse()

    # read in dictionary (metadata structure)
    d = os.path.join(DATADIR, DICTIONARY)
    g3dict = Gen3Dictionary(d)
    schema = g3dict.parse()

    validator = AGDRSchema(schema, rs_data)
    validator.validate()
