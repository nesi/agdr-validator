from enum import Enum
import json

DATADIR = "/Users/eirian/NeSI/2023-01-17-metadata-spreadsheet-validation/excelParser/test/data"
DICTIONARY = "gen3.nesi_2022_09_23.json"

Multiplicity = Enum('Multiplicity', 
    [
        'ONE_TO_ONE', 
        'ONE_TO_MANY', 
        'MANY_TO_ONE', 
        'MANY_TO_MANY'
    ])

class PrototypeDictionaryReader():
    def __init__(self):
        self._dictionary = {}
        self._root = None
        # Gen3 specific
        self._definitions = None
        self._settings = None
        self._terms = None

    def pprint(self, jdata=None):
        # pretty print Python dictionary as JSON
        if not jdata:
            jdata = self._dictionary
        print(json.dumps(jdata, indent=4))

    def _extractRoot(self):
        for key in self._dictionary.keys():
            if key in [
                "_definitions.yaml",
                "_settings.yaml",
                "_terms.yaml"
            ]:
                continue
            if "links" not in self._dictionary[key] or not self._dictionary[key]["links"]:
                print(f"root node: {key}")
                self._root = self._dictionary[key]
                # mutate dictionary to remove root node
                self._dictionary.pop(key)
                break

    def _extractChildren(self, node):
        children = []
        keys = list(self._dictionary.keys())
        for key in keys:
            if key in [
                "_definitions.yaml",
                "_settings.yaml",
                "_terms.yaml"
            ]:
                continue
            if "links" in self._dictionary[key] and self._dictionary[key]["links"]:
                for link in self._dictionary[key]["links"]:
                    #print(link.keys())
                    if "target_type" in link and link["target_type"] == node["id"]:
                        #children.append({key: self._dictionary[key]})
                        children.append(self._dictionary[key])
                        self._dictionary.pop(key)
                        self.pprint(link)
                    elif not "target_type" in link:
                        print(f"unhandled node type: {self._dictionary[key]['id']}")
                        self.pprint(link)
        return children

    def readDictionary(self, dictionary_path):
        raw_json = None
        with open(dictionary_path, 'r') as f:
            raw_json = f.readlines()
        raw_json = "\n".join(raw_json)
        raw_schema = json.loads(raw_json)
        self._dictionary = raw_schema
        #print(json.dumps(raw_schema, indent=4))
        #for key in raw_schema.keys():
        #    print(key)

        # assume program.yaml is the root node

        #self.pprint(jdata=raw_schema["program.yaml"])
        #self.pprint(jdata=raw_schema["project.yaml"])
        self._extractRoot()
        #self._root = raw_schema["program.yaml"]

        # need to loop through all the keys to see which have a link 
        # to program.yaml
        # or could create dictionary -> list where 
        #   keys are parent node and values are list of children
        # then iterate through the dictionary starting from root node
        #
        # how to handle multiple edges, e.g. 2 parent nodes
        #   need to know if edge is required or not
        rootChildren = self._extractChildren(self._root)
        print("root children:")
        #for child in rootChildren:
        #    print(list(child.keys())[0])

        for rootChild in rootChildren:
            print(f"root child: {list(rootChild.keys())[0]}")
            #rootChildChildren = self._extractChildren(self._dictionary[list(rootChild.values())[0]])
            rootChildChildren = self._extractChildren(rootChild)
            print(f"root child {rootChild['id']} children:")
            for child in rootChildChildren:
                print(child["id"])


        # I also have to think about subgroups, and whether 
        # any of them are required
        #   if NONE are required, but required is true, then AT LEAST ONE
        #   is required

        # but at least now I can recursively extract child nodes