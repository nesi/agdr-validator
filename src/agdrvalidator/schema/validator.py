'''
@Author: Eirian Perkins

The validator needs a schema type that has both a gen3schema 
(dictionary parsing output) and the associated metadata read in from 
an excel spreadsheet (AGDRSchema). This will have the logic to create a graph 
structure from the custom schema using the gen3schema structure.

This file provides an abstract base class for a particular version 
of a validator.
'''

import abc

from agdrvalidator.schema.agdrschema_2022_09_23 import AGDR as AGDRSchema
from agdrvalidator.schema.gen3schema import Gen3 as Gen3Schema
from agdrvalidator.schema.base import Schema


class Validator(Schema):
    def __init__(self, gen3schema, agdrschema):
        self._gen3schema = gen3schema
        self._agdrschema = agdrschema

    @abc.abstractmethod 
    def getRootNode(self):
        pass

    @abc.abstractmethod 
    def walk(self):
        pass