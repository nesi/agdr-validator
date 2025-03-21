from enum import Enum

from agdrvalidator.schema.node.property import *
from agdrvalidator.utils import logger

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
    
    def reset_fields(self):
        self._name = None
        self._input_name = None
        self._value = None
        self._required = None
        self._type = None
        self._pattern = None