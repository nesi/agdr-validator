'''
@Author Eirian Perkins

this file contains data container classes used to represent 
metadata from excel workbook input, together with its 
Gen3 metadata dictionary analogue, from the 2024_09_10.json version 
of the AGDR dictionary.
'''

from agdrvalidator.utils.rich_tabular import CellLocation, SpreadsheetProperty
from agdrvalidator.schema.node.property.gen3property import *
from agdrvalidator import * # import AGDR exception types


class AGDR(SpreadsheetProperty):
    '''
    This class represents data for a single cell, including 
    the header name (self.name) and value (self.data).

    If the SpreadsheetProperty has no data, then it represents a 
    header cell
    '''

    @classmethod
    def convertName(_, name):
        # this should already have been done by AGDRNode objects
        # name is what's in the spreadsheet 
        # gen3_name is what's in the Gen3 dictionary
        raise AgdrNotImplementedException("I don't know how to convert names yet") 

    def __init__(self, property:SpreadsheetProperty, rule:Gen3):
        self.name = None
        self.data = None
        self.location = CellLocation(None, None)
        self.required = False
        if property:
            self.name = property.name # name from spreadsheet
            self.data = property.data
            self.location = property.location
            self.required = property.required
            if rule:
                self.required = property.required or rule.isRequired()
        self.gen3_name = None
        self.rule = rule # a Gen3 property
        # TODO: investigate missing `rule` properties (None passed in frequently)
        if rule:
            #self.gen3_name = rule._input_name
            self.gen3_name = rule._name # output name
            self.required = rule.isRequired()
            if property:
                self.required = property.required or rule.isRequired()

    def __str__(self):
        return f"Name: {self.name},Gen3Name: {self.gen3_name}, Value: {self.data}, Location: ({self.location}), Required: {self.required}, Gen3Property: {self.rule}"

    def __repr__(self):
        return f"AGDRProperty(name={self.gen3_name}, gen3name={self.gen3_name}, value={self.data}, cell_location=CellLocation({self.location}), required={self.required}, gen3property={self.rule})"
        #return f"AGDRProperty(name={self.name}, value={self.data}, cell_location=CellLocation({self.location}), required={self.required})"


    def get_value(self):
        return self.data