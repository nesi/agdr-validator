
# pytest -s
# to see stdout for all tests

from agdrvalidator.parser.excel.agdrspreadsheet import *

import pandas as pd
import pytest
import random
import string
import tempfile
import os


DATADIR = "test/data/old"
VENENIVIBRIO = "AGDR_Metadata_Venenivibrio.xlsx"
HOIHO = "AGDR_00029_Metadata_Hoiho_202208.xlsx"

def get_random_string(length):
    # With combination of lower and upper case
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
    return result_str

def randomly_uppercase_letters(text):
    return ''.join([c.upper() if random.randint(0,1) else c for c in text])

def write_blank_excel(filename):
    # create blank excel file
    df = pd.DataFrame()
    df.to_excel(filename)



@pytest.mark.parametrize("extension", [get_random_string(random.randint(3,6)) for x in range(0,100)] )
def test_fileExtension_sadpath(extension):
    # reject file extension that is not .xlsx
    # test with 100 random file extensions

    while extension.lower() == "xlsx":
        extension = get_random_string()
        
    # reject file extension that is not .xlsx
    print(f"testing file extension {extension}")
    agdrInstantiated = False
    try:
        _ = Agdr(f"foo.{extension}")
        agdrInstantiated = True
    except Exception as e:
        assert(str(e) == "File extension must be .xlsx")
    assert not agdrInstantiated


def test_excel_format_sadpath(extension="xlsx"):
    # test that a blank file does not have the proper format for reading in with pandas

    # create temporary file
    tmpfile = tempfile.NamedTemporaryFile(suffix=f".{extension}")
    with open (tmpfile.name, "w") as f:
        f.write("this is a plaintext file")

    print(f"tmpfile: {tmpfile.name}")
    agdrInstantiated = False
    try:
        _ = Agdr(tmpfile.name)
        agdrInstantiated = True
    except AgdrFormatException as e:
        # excel opened but doesn't have the expected worksheets
        agdrInstantiated = True
    except Exception as e:
        # excel cannot be read
        print(e)
        assert(str(e) == "Excel file format cannot be determined, you must specify an engine manually.")
    assert not agdrInstantiated


@pytest.mark.parametrize("extension", [randomly_uppercase_letters("xlsx") for x in range(0,20)] )
def test_fileExtension_happypath(extension):
    # accept file extension with case insensitive .xlsx 

    # create temporary file
    tmpfile = tempfile.NamedTemporaryFile(suffix=f".{extension}")
    write_blank_excel(tmpfile)

    print(f"tmpfile: {tmpfile.name}")
    agdrInstantiated = False
    try:
        _ = Agdr(tmpfile.name)
        agdrInstantiated = True
    except AgdrFormatException as e:
        # excel opened but doesn't have the expected worksheets
        agdrInstantiated = True
    except Exception as e:
        pass
    assert agdrInstantiated


# tests:
# - user removed rows 
#   - required 
#   - description
#   - example input 
#   - instructions and tips (and lines below)
#   - project information header
# - user removed columns
# - no rows, columns removed
# - user swaps order of experiments, biosamples, etc

def test_parsing_excel_VENENIVIBRIO_happypath():
    excel = os.path.join(DATADIR, VENENIVIBRIO)
    agdr = Agdr(excel)
    agdr.parse()
    # TBD: validate data (have done this manually)
    ############################
    ############################
    print("_____")
    print("Project Info:")
    print("_____")
    for item in agdr.Project.data:
        print(f"{item}\n")

    print("_____")
    print("Experiment and sample info:")
    print("_____")
    print("Experiments")
    for item in agdr.Experiments.data:
        print(f"{item}\n")
    print("")
    print("Organism")
    for item in agdr.Organism.data:
        print(f"{item}\n")
    print("")
    print("Environmental")
    for item in agdr.Environmental.data:
        print(f"{item}\n")

    print("_____________________")
    print("_____")
    print("Files and Instruments:")
    print("")
    print("Files")
    for item in agdr.Files.data:
        print(f"{item}\n")
    print("Instrument Metadata")
    for item in agdr.InstrumentMetadata.data:
        print(f"{item}\n")
    print("_____")