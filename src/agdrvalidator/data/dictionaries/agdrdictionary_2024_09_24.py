import os 
from agdrvalidator.parser.dictionary.gen3parser import Gen3 as Gen3Dictionary

# how to get loading data file to work:
# https://stackoverflow.com/a/57749691

def loadDictionary():
    location = os.path.dirname(os.path.realpath(__file__))
    dict_file = os.path.join(location, "gen3.nesi_2024_09_24.json")
    g3dict = Gen3Dictionary(dict_file)
    schema = g3dict.parse()
    return schema