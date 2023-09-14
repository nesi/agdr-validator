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
            "name": "submitter_id",
            "sample_id": "submitter_id"
        }
        if result in lookup:
            return lookup[result]
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

    def _is_required_and_valid(self):
        '''
        check if property is required, and if it is, is there a value?
        '''
        reason = None 
        valid = True
        if not self._rule:
            required = False
            logger.warning(f"No rule found for property {self._output_name}, assuming not required")
        else:
            required = self._rule._isRequired
        logger.debug(f"property {self._output_name}: {self._value} is required? {required}")

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