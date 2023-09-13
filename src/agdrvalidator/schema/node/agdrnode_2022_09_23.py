from agdrvalidator.utils import logger
from agdrvalidator.schema.node import *

logger = logger.setUp(__name__)

class AGDR(Node):
    @classmethod
    def convertName(cls, name):
        '''
        may not be needed
        '''
        name = name.lower()
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
        logger.debug(f"Created Node: {name}")

    def _validate_properties(self):
        node_valid = True
        invalid_properties = {}
        for property in self._properties:
            property_valid, reason = property.validate()
            if not property_valid:
                node_valid = False
                invalid_properties[property] = reason
            if node_valid:
                logger.debug(f"\t\t[  valid  ]: {property._output_name}... {node_valid}")
            else:
                logger.debug(f"\t\t[  PROPERTY INVALID  ]: {property._output_name}... {node_valid}")
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

    def addProperty(self, property):
        self._properties.append(property)

    def getProperties(self):
        return self._properties

    def isParent(self):
        raise NotImplementedError