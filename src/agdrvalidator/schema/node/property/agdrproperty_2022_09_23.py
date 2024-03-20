'''
@Author: Eirian Perkins

This file models properties of nodes from the AGDR data dictionary 
version 2022-09-23. All nodes have a collection of properties, which 
have a name, value, type, and possibly a regex pattern. A property
may or may not be required. A required property must have a value.
'''
import re

from agdrvalidator.utils import logger
from agdrvalidator.schema.node.property import *

logger = logger.setUp(__name__)


class AGDR(Property):
    @classmethod
    def convertName(cls, name):
        # remove emphasis or indication
        logger.debug(f"convertName: input: {name}")
        result = str(name).strip("*").lower().strip()
        lookup = {
            # Experiments
            'name or id': 'submitter_id',
            #'associated_experiment': None, # ??? no corresponding property
            #'associated_references': None, # need to handle this, it is a publication node
            # Environmental
            # other stuff
            'sample_id': 'submitter_id',
            'experiments': 'experiments.submitter_id'
            #"name": "submitter_id", # don't override, this is for property.name
            #'associated_experiment': 'type_of_specimen' # incorrect
        }
        if result in lookup:
            return lookup[result]

        #if ("associated_" in name):
        #    _, parent = name.split("_")
        #    return parent + ".submitter_id"

        return result

    def __init__(self, name, value, gen3property):
        super().__init__(name, value)
        # name: name of a header in the spreadsheet
        # output name: name of a property in the Gen 3 schema
        self._output_name = self.convertName(name)
        self._rule = gen3property # gen3property.Gen3 type

        logger.debug("---Creating property...")
        logger.debug(f"\t\t name: {name}")
        logger.debug(f"\t\t value: {value}")
        logger.debug(f"\t\t gen3prop: {str(gen3property)}")


    def _is_pattern_valid(self):
        reason = None
        valid = True
        # TODO TODO TODO TODO
        # enable code below
        #
        # for now, not performing validation, because parsing is 
        # incorrect (and assigning patterns to incorrect properties)
        return valid, reason

        if not self._rule._pattern:
            return True, None
        else:
            pattern = self._rule._pattern
            value = self._value
            #print(f"pattern: {self._rule._pattern}")
            #print(f"value:   {self._value}")
            #print(f"name:    {self._name}")
            #print(f"g3value: {self._rule._value}")
            #print(f"g3name:  {self._rule._name}")
            if re.findall(pattern, value):
                # this implementation seems correct, but parsing 
                # property values isn't working correctly, need to fix 
                # before proceeding
                return True, None
            else:
                return False, f"Property <{self._rule._name}> with value <{value}> does not conform to regex pattern <{pattern}>"
            #raise Exception("Pattern application not yet implemented")

    def _is_enum_valid(self):
        allowed_values = self._rule._type['enum']
        value = self._value
        isValid = False
        reason = None
        for av in allowed_values:
            if str(value).lower() == str(av).lower():
                self._value = av
                isValid = True
                reason = None
        if not isValid:
            reason = f"Expecting value to be in {str(allowed_values)}, but received [{value}] instead"
            #raise Exception(reason)

        return isValid, reason


    def _is_boolean_valid(self):
        '''
        it would be nice to have a "warn" level here instead of just yes/no whether
        the value is valid. May want to have more verbose output showing what was the 
        input value and what was it transformed into.

        the agdrschema has some logic to "boolify" values. This may not always
        do what we want it to.
        '''
        isValid = True 
        reason = None
        falsy = ['false', 'f', 'no', 'n', '0']
        truthy = ['true', 't', 'yes', 'y', '1']
        if self._value.lower() in falsy:
            self._value = False
        elif self._value.lower() in truthy:
            self._value = True
        else:
            isValid = False 
            reason = f"Expected a boolean value, but received [{self._value}] instead"
        return isValid, reason


    def _is_integer_valid(self):
        isValid = True 
        reason = None
        try:
            value = int(self._value)
            self._value = value
        except ValueError as e:
            isValid = False 
            #reason = e
            reason = f"Expected an integer value, but received [{self._value}] instead"
        return isValid, reason


    def _is_number_valid(self):
        isValid = True 
        reason = None
        try:
            value = float(self._value)
            self._value = value
        except ValueError as e:
            isValid = False 
            #reason = e
            reason = f"Expected a numeric value, but received [{self._value}] instead"
        return isValid, reason


    def _are_multiple_allowable_types_valid(self, types):
        isValid = False 
        reason = None 
        value = self._value 
        if not value:
            if 'null' in types:
                isValid = True
        elif 'string' in types:
            isValid = True 
        elif 'integer' in types:
            isValid, reason = self._is_integer_valid()
        elif 'boolean' in types:
            isValid, reason = self._is_boolean_valid()
        elif 'number' in types:
            isValid, reason = self._is_number_valid()
        else:
            raise Exception(f"unknown type(s): {types}")
        return isValid, reason
 
        

    def is_required(self):
        if not self._rule:
            required = False
            logger.debug(f"No rule found for property {self._output_name}, assuming not required")
        else:
            required = self._rule._isRequired
        logger.debug(f"property {self._output_name}: {self._value} is required? {required}")
        return required

    def _is_required_and_valid(self):
        '''
        check if property is required, and if it is, is there a value?
        '''
        reason = None 
        valid = True

        required = self.is_required()

        pattern = None
        type = None
        g3value = None
        g3name = None
        if self._rule:
            pattern = self._rule._pattern
            type = self._rule._type
            g3value = self._rule._value
            g3name = self._rule._name

        logger.debug(f"___pattern: {pattern}")
        logger.debug(f"___type:    {type}")
        logger.debug(f"___value:   {self._value}")
        logger.debug(f"___g3value: {g3value}")
        logger.debug(f"___name:    {self._name}")
        logger.debug(f"___g3name:  {g3name}")


        if not required and self._value == None:
            # not required and no value provided
            valid = True
            reason = None
        elif self._value == None:
            # required and no value provided
            valid = False 
            reason = f"Property {self._output_name} is required, but no value was provided"
        else:
            # either required and value provided, or not required and value provided
            if str(type).lower() == "string":
                if pattern:
                    valid, reason = self._is_pattern_valid()
                else:
                    valid = True 
                    reason = None
            elif str(type).lower() == "boolean":
                valid, reason = self._is_boolean_valid()
            elif str(type).lower() == "integer":
                valid, reason = self._is_integer_valid()
            elif str(type).lower() == "number":
                valid, reason = self._is_number_valid()
            if isinstance(type, dict):
                if 'enum' in type:
                    valid, reason = self._is_enum_valid()
            elif isinstance(type, list):
                #___type:    ['string', 'null']
                valid, reason = self._are_multiple_allowable_types_valid(type)

        # if type is None, there is a problem

        # TODO
            # next need to check type
                # integer 
                # boolean
                # ...
        '''
        (venv) eirian> agdrvalidator -s AGDR_Metadata_Venenivibrio.xlsx --stdout -v | grep "___type:" | sort | uniq
        ___type:    None
        ___type:    ['string', 'null']
        ___type:    boolean
        ___type:    integer
        ___type:    number
        ___type:    string
        '''

        #if not required:
        #    # this is not correct, need to see if there is a value first
        #    valid = True
        #    reason = None
        #elif self._value == None:
        #    valid = False 
        #    reason = f"Property {self._output_name} is required, but no value was provided"
        #else:
        #    # check pattern
        #    valid, reason = self._is_pattern_valid()

        # cases:
            # string with pattern
            # just a type (string, integer, etc)
            # an enum

        return valid, reason

    def validate(self):
        # don't need this debugging
        #print(f"\tprop name: {self._output_name}")
        #if self._rule:
        #    print(f"\t\ttype: {self._rule._type}")
        #    print(f"\t\tpatt: {self._rule._pattern}") # BUG: none of the patterns are populated, be sure to fix this
        #    print(f"\t\treqd: {self._rule._isRequired}")
        #else:
        #    print(f"\t\ttype: {self._rule}")

        # return True, None if property valid
        # return False, error string if property not valid
        reason = None
        valid = True

        # check if required, and if so, if value is valid
        #       internally calls self._is_pattern_valid()
        valid, reason = self._is_required_and_valid()

        # check type 
        #   TODO

        return valid, reason

    def __str__(self):
        representation = {
            "name": self._input_name,
            "value": self._value,
            #"required": self._isRequired,
            #"type": self._type,
            #"pattern": self._pattern
        }
        return str(representation)

    def __repr__(self):
        return self.__str__()