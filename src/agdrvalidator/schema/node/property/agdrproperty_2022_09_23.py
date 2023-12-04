from agdrvalidator.utils import logger
from agdrvalidator.schema.node.property import *

logger = logger.setUp(__name__)


class AGDR(Property):
    @classmethod
    def convertName(cls, name):
        # remove emphasis or indication
        logger.debug(f"convertName: input: {name}")
        result = name.strip("*").lower().strip()
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
        if not self._rule._pattern:
            return True, None
        else:
            raise Exception("Pattern application not yet implemented")

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

        if not required:
            valid = True
            reason = None
        elif self._value == None:
            valid = False 
            reason = f"Property {self._output_name} is required, but no value was provided"
        else:
            # check pattern
            valid, reason = self._is_pattern_valid()

        return valid, reason

    def validate(self):
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