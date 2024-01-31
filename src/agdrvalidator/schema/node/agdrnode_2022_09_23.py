from agdrvalidator.utils import logger
from agdrvalidator.schema.node import *
from agdrvalidator.schema.node.property.agdrproperty_2022_09_23 import AGDR as AGDRProperty
from agdrvalidator import AgdrImplementationException

logger = logger.setUp(__name__)

class AGDR(Node):
    @classmethod
    def convertName(cls, name):
        '''
        may not be needed
        '''
        name = name.lower().strip()
        lookup = {
            "environmental": "metagenome"
        }
        if name in lookup:
            return lookup[name]
        return name

    def __init__(self, name, gen3node):
        # creates self._properties, _parents, and _children
        super().__init__()
        self._input_name = name
        self._output_name = self.convertName(name)
        self._gen3_node = gen3node
        self._unique_id = None # set when the property is added
        # self._properties is an empty list
        logger.debug(f"Created Node: {name}")

    def _validate_properties(self):
        node_valid = True
        invalid_properties = {}
        for property in self._properties:
            property_valid, reason = property.validate()

            if not property_valid:
                node_valid = False
                invalid_properties[property._output_name] = reason
            #if node_valid:
            if property_valid:
                req = False 
                if property._rule:
                    req = property._rule._isRequired
                logger.info(f"\t\t[  valid  ]: {property._output_name}... {property_valid}")
                #logger.info(f"\t\t[  valid  ]: {property._output_name}... {property_valid} ... required? {req}")
            else:
                logger.info(f"\t\t[  PROPERTY INVALID  ]: {property._output_name}... {node_valid}")
        return node_valid, invalid_properties

    def validate(self):
        # check if properties are valid
        node_valid, reasons = self._validate_properties()

        # check if node has proper required links 
        # TODO

        # check node multiplicity
        # TODO

        return node_valid, reasons

    def walk(self):
        raise NotImplementedError

    def getParents(self):
        raise NotImplementedError

    def getChildren(self):
        raise NotImplementedError

    def addParent(self, parent, multiplicity=None):
        raise NotImplementedError

    def addChild(self, child, multiplicity=None):
        raise NotImplementedError

    def addPropertyDeprecated(self, property):
        self._properties.append(property)
        if property._output_name == "submitter_id":
            self._unique_id = property._value

    def addProperty(self, property):
        '''
        if property already exists, replace it with the new one

        there is a one-off problem for Environmental nodes, where 
        Type is requested in the spreadsheet template. This is a bug, 
        because the type should always be Environmental
        '''
        # one-off fix: ignore "associated_experiment"
        # experiments cannot be linked, this is a bug in the spreadsheet template
        logger.debug(f"received property: {property}")
        if property._input_name == "associated_experiment":
            return

        idx, prop = self._getPropertyAndIndex(property._output_name)
        if idx is not None:
            logger.debug(f"Replacing property {property._output_name} with new value {property._value}")
            self._properties[idx] = property
            logger.debug(f"node name: {self._output_name}")
            if self._output_name == "experiment":
                replaced_prop = AGDRProperty("type_of_specimen", prop._value, prop._rule)
                self._properties.append(replaced_prop)
        else:
            self._properties.append(property)
        if property._output_name == "submitter_id":
            self._unique_id = property._value


    def removeProperty(self, name):
        allowable_nodes_and_props = {}
        allowable_nodes_and_props["metagenome"] = ["lat_lon", "sample_type", "organism", "isolation_source", "temperature", "ph"]
        allowable_nodes_and_props["organism"] = ["lat_lon"]
        allowable_nodes_and_props["experiment"] = ["associated_references"]
        #allowable_nodes_and_props["processed_file"] = []
        allowable_nodes_and_props["raw"] = ["corresponding_sample_id", "submitter_id"]
        allowable_nodes_and_props["processed_file"] = ["associated_references", "corresponding_sample_id", "submitter_id"]
        allowable_nodes_and_props["experimental_metadata"] = ["submitter_id", "corresponding_sample_id"]
        allowable_nodes_and_props["read_group"] = ["corresponding_sample_id"]

        if self._output_name in allowable_nodes_and_props:
            allowable_props = allowable_nodes_and_props[self._output_name]
            if len(allowable_props) == 0 or name in allowable_props:
                # all good
                idx, prop = self._getPropertyAndIndex(name)
                if idx is not None:
                    prop = self._properties.pop(idx)
                return prop
            else:
                raise AgdrImplementationException("Cannot remove property")

        else:
            raise AgdrImplementationException("Cannot remove property")


    def getProperties(self):
        return self._properties

    def _getPropertyAndIndex(self, name):
        for idx, property in enumerate(self._properties):
            if property._output_name == name or property._name == name:
                return idx, property
        return None, None

    def getProperty(self, name):
        _, property = self._getPropertyAndIndex(name)
        return property

    def isParent(self):
        raise NotImplementedError

    def generateSubmitterId(self, parent_submitter_id=None):
        mytype = self.getProperty("type")#._value
        if mytype:
            mytype = mytype._value
        else:
            mytype = self._output_name
        submitter_id = parent_submitter_id
        if not parent_submitter_id:
            projectid = self.getProperty("projects.code")#._value
            if not projectid:
                projectid = self.getProperty("project_id")
            else:
                projectid = projectid._value
            if not projectid and mytype != "raw" and mytype != "processed_file" and mytype != "experimental_metadata":
                raise Exception("Cannot generate submitter_id, no project_id found")
            submitter_id = projectid
        if mytype == "core_metadata_collection":
            submitter_id = f"{submitter_id}_CMC01"
        elif mytype == "sample":
            submitter_id = f"{submitter_id}_SAMPLE"
        elif mytype == "aliquot":
            submitter_id = f"{submitter_id}_ALQ"
        elif mytype == "publication":
            submitter_id = f"{submitter_id}_PUB"
        elif mytype == "raw" or mytype == "processed_file":
            submitter_id = self.getProperty("file_name")._value
        elif mytype == "read_group":
            submitter_id = f"{submitter_id}_RG"
        elif mytype == "experimental_metadata":
            submitter_id = self.getProperty("file_name")._value
        return submitter_id
