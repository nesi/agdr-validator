#from enum import Enum
import json

from alive_progress import alive_bar

from agdrvalidator import AgdrFormatException
from agdrvalidator.parser import *
from agdrvalidator.schema import gen3schema as schema
from agdrvalidator.schema.node import gen3node as node
from agdrvalidator.utils import logger

logger = logger.setUp(__name__)

class Gen3(Parser):
    '''
    this knows how to parse a Gen3 dictionary down to nodes 

    nodes know how to parse their properties
    '''
    def __init__(self, datapath):
        super().__init__(datapath)
        self._schema = schema.Gen3()
        self._gen3Dictionary = self._openDictionary()


    def _openDictionary(self):
        dpath = self.datapath.split("/")[-1]
        dextension = dpath.split(".")[-1]
        logger.debug(f"file extension: {dextension.lower()}")
        if not dextension.lower() == "json":
            raise Exception("File extension must be .json")

        # see if structure matches Gen 3 expectations
        with open(self.datapath, 'r') as f:
            raw_json = f.readlines()
        raw_json = "\n".join(raw_json)
        raw_schema = json.loads(raw_json) 
        try:
            self._schema.setDefinitions(raw_schema["_definitions.yaml"])
            raw_schema.pop("_definitions.yaml")
            self._schema.setSettings(raw_schema["_settings.yaml"])
            raw_schema.pop("_settings.yaml")
            self._schema.setTerms(raw_schema["_terms.yaml"])
            raw_schema.pop("_terms.yaml")
        except:
            raise AgdrFormatException("File is not a Gen3 dictionary")

        return raw_schema

    def _extractRoot(self):
        # extract the root node from self._gen3Dictionary
        # root is removed from self._gen3Dictionary and returned
        root = None
        for key in self._gen3Dictionary.keys():
            # if these haven't been extracted there is an error
            assert key not in [
                "_definitions.yaml",
                "_settings.yaml",
                "_terms.yaml"
            ]
            if "links" not in self._gen3Dictionary[key] or not self._gen3Dictionary[key]["links"]:
                logger.debug(f"root node: {key}")
                root = self._gen3Dictionary[key]
                # there should be no other nodes without children
                assert root["id"].lower() == "program"
                # mutate dictionary to remove root node
                self._gen3Dictionary.pop(key)
                break
        root = node.Gen3(root, root["id"])
        self._schema.setRoot(root)
        return root

    def parse(self):
        root = self._extractRoot()
        self._schema.setRoot(root)
        current_depth = [root]
        next_depth = []

        with alive_bar(title="\tLoading data dictionary ") as bar:
            while current_depth != []:
                for current_node in current_depth:
                    self._schema.nodes[current_node.name] = current_node
                    for potential_child in list(self._gen3Dictionary):
                        pchild_node = node.Gen3(self._gen3Dictionary[potential_child], self._gen3Dictionary[potential_child]["id"])
                        logger.debug(f"_____checking node: [____{pchild_node.name}____] with potential parent: {current_node.name}")
                        if pchild_node.isChildOf(current_node):
                            logger.debug(f"found child of {current_node.name}: {pchild_node.name}")

                            logger.debug(f"_____{pchild_node.name}______")
                            pchild_node.parse_properties(self._gen3Dictionary[potential_child]["properties"], self._gen3Dictionary[potential_child]["required"], self._schema._terms, self._schema._definitions, self._schema._settings)
                            current_node.addChild(pchild_node)
                            pchild_node.addParent(current_node)
                            next_depth.append(pchild_node)
                            self._gen3Dictionary.pop(potential_child)
                            bar()
                else:
                    current_depth = next_depth
                    next_depth = []

            # do some post processing; 
            # some parent / child relationships may have been skipped over
            for n in self._schema.nodes.values():
                for parent_link in n.getParentLinks():
                    n.addParent(self._schema.nodes[parent_link.node_id])
                    self._schema.nodes[parent_link.node_id].addChild(n)
                    bar()

        return self._schema