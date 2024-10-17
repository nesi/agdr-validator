from agdrvalidator.utils import logger
from agdrvalidator.schema.node.property import *
from enum import Enum

logger = logger.setUp(__name__)

PropertyType = Enum("PropertyType",
    [
        'BOOL',
        'STRING',
        'INTEGER',
        'ENUM',
        'ARRAY',
        'NULL',
        'OBJECT'
    ])

# maybe want to have a "Rule" class
# e.g. a TypeRule will check the type 
#        PatternRule will apply regex 
#        RequiredRule will check if a property is required
#        ManyRule will check one-to-* and many-to-* relationships
#        (many applies to nodes not properties)
#        etc.

class Gen3(Property):
    def __init__(self, name, value=None, required=False, type=None, pattern=None):
        super().__init__(name, value)
        self._type = type # PropertyType TODO make sure it was populated correctly
        self._pattern = pattern # regex
        self._isRequired = bool(self._input_name in required)


    def __str__(self):
        representation = {
            "name": self._name,
            "_input_name": self._input_name,
            "value": self._value,
            "required": self._isRequired,
            "type": self._type,
            "pattern": self._pattern
        }
        return str(representation)

    def __repr__(self):
        return self.__str__()

    def isRequired(self):
        return self._isRequired