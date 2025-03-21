'''

this file contains data container classes used to represent 
metadata from excel workbook input, together with its 
Gen3 metadata dictionary analogue, from the 2025_01_24.json version 
of the AGDR dictionary.
'''

import numbers
import re

from agdrvalidator import *  # import AGDR exception types
from agdrvalidator.schema.node.property.gen3property import *
from agdrvalidator.utils import is_nan
from agdrvalidator.utils.rich_tabular import CellLocation, SpreadsheetProperty


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


    def validate(self):
        """Validates the property data based on the Gen3 rule."""
        if not self.rule:
            # No rule specified for validation; assume valid.
            return True, None

        # Initialize validation result
        valid = True
        reason = None

        is_empty = self.data is None or self.data == "" or is_nan(self.data)
        if is_empty:
            # purge the nans
            self.data = None

        if not self.required and is_empty:
            return valid, reason
        elif self.required and is_empty:
            return False, f"Required field '{self.name}' is missing"

        # 1. Pattern Validation (if applicable)
        if self.rule._pattern:
            pattern_valid, reason = self._is_pattern_valid()
            if not pattern_valid:
                return False, reason

        # 2. Type Validation
        type_info = self.rule._type
        if isinstance(type_info, dict):
            if 'enum' in type_info:
                valid, reason = self._is_enum_valid()
            else:
                valid, reason = False, f"Unsupported type {type_info.get('type')}"
        elif isinstance(type_info, list):
            # Handle cases with multiple types allowed (e.g., ["string", "null"])
            valid, reason = self._are_multiple_allowable_types_valid(type_info)
        elif type_info == "boolean":
            valid, reason = self._is_boolean_valid()
        elif type_info == "integer":
            valid, reason = self._is_integer_valid()
        elif type_info == "number":
            valid, reason = self._is_number_valid()
        elif type_info == "string":
            # Handle string type, even if there's no pattern specified
            valid, reason = self._is_string_valid()
        else:
            valid, reason = False, f"Unknown type {type_info}"

        return valid, reason

    def _is_string_valid(self):
        """Validates that the property data is a string, setting it to an empty string if it's None or NaN."""
        if self.data is None or is_nan(self.data):
            self.data = ""  # Set to an empty string if None or NaN
        else:
            self.data = str(self.data)  # Ensure the value is treated as a string
        
        # Since pattern application is handled separately, any string is valid here
        return True, None

    def _is_pattern_valid(self):
        """Validates the property data against a regex pattern if specified."""
        free_strings = [
            "submitter_id",
            "file_name",
            "habitat",
            "geo_loc_name",
            "environmental_medium",
            "collected_by",
            "secondary_identifier",
            "store_cond"
        ]
        actually_integers = [
            "file_size",
            "latitude_decimal_degrees",
            "longitude_decimal_degrees"
        ]
        actually_floats = [
            "coordinate_uncertainty_in_meters",
        ]
        '''
        environmental_medium
        '''

        # some dictionary parsing is wrong, here are some hacks to
        # make it work in the mean time
        if self.gen3_name in actually_integers:
            return self._is_integer_valid()

        if self.gen3_name in free_strings:
            # currently a UUID regex is applied, but it should be any string
            return True, None

        if self.gen3_name in actually_floats:
            return self._is_number_valid()

        if not self.rule._pattern:
            return True, None
        pattern = self.rule._pattern
        self.rule._pattern = r'{}'.format(pattern)
        if re.fullmatch(self.rule._pattern, str(self.data)):
            return True, None
        else:
            return False, f"Value {self.name}; {self.gen3_name} '{self.data}' does not match pattern '{self.rule._pattern}'"

    def _is_enum_valid(self):
        """Validates if the property data is within allowed enum values."""
        allowed_values = self.rule._type.get('enum', [])
        for av in allowed_values:
            if str(self.data).lower().strip() == str(av).lower():
                self.data = str(av)  # Set self.data to the correctly formatted value
                return True, None
        #if str(self.data).lower().strip() in (str(av).lower() for av in allowed_values):
            #self.data = str(self.data).lower().strip()
            #return True, None
        return False, f"Value '{self.data}' is not in allowed values {allowed_values}"

    def _is_boolean_valid(self):
        """Checks if the property data can be interpreted as a boolean."""
        if isinstance(self.data, bool):
            return True, None
        truthy = {'true', 't', 'yes', 'y', '1'}
        falsy = {'false', 'f', 'no', 'n', '0'}
        data_str = str(self.data).lower()
        if data_str in truthy:
            self.data = True
            return True, None
        elif data_str in falsy:
            self.data = False
            return True, None
        return False, f"Expected boolean value but got '{self.data}'"

    def _is_integer_valid(self):
        """Validates if the property data is an integer."""
        actually_floats = [
            "latitude_decimal_degrees",
            "longitude_decimal_degrees"
        ]
        if self.gen3_name in actually_floats:
            return self._is_number_valid()

        try:
            self.data = int(self.data)
            return True, None
        except ValueError:
            return False, f"Expected integer but got '{self.data}'"

    def _is_number_valid(self):
        """Validates if the property data is numeric."""
        try:
            self.data = float(self.data)
            return True, None
        except ValueError:
            return False, f"Expected numeric value but got '{self.data}'"

    def _are_multiple_allowable_types_valid(self, types):
        """Validates property data against multiple allowed types."""
        if self.data is None and 'null' in types:
            return True, None
        if 'string' in types and (isinstance(self.data, str) or isinstance(self.data, numbers.Number)):
            return True, None
        if 'integer' in types:
            return self._is_integer_valid()
        if 'boolean' in types:
            return self._is_boolean_valid()
        if 'number' in types:
            return self._is_number_valid()
        return False, f"Value '{self.data}' does not match any allowed types {types}"