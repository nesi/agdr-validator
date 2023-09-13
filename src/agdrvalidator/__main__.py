import agdrvalidator.utils.investigation as ivst
import agdrvalidator.schema.investigation as divst
from agdrvalidator.parser.dictionary.gen3parser import Gen3 as Gen3Dictionary
from agdrvalidator.parser.excel.agdrspreadsheet import *
import os

def main():
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

    DATADIR = "test/data"
    DICTIONARY = "gen3.nesi_2022_09_23.json"
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

if __name__ == "__main__":
    main()