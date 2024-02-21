'''
@Author: Eirian Perkins

need a schema type that has both a gen3schema and an agdrschema
this will have the logic to create a graph structure from the 
agdr schema using the gen3schema

A lot of the work is already done in agdrschema_2022_09_23.py, but 
ideally the validator class should do all the work to relate the
two schemas together.
'''

from agdrvalidator.utils import logger 
from agdrvalidator.schema.agdrschema_2022_09_23 import AGDR as AGDRSchema
from agdrvalidator.schema.gen3schema import Gen3 as Gen3Schema
from agdrvalidator.schema.base import Schema as Schema

logger = logger.setUp(__name__)

class AGDRValidator(Schema):
    def __init__(self, gen3schema, agdrschema):
        self._gen3schema = gen3schema # contains dictionary structure
        self._agdrschema = agdrschema # contains metadata
        self._root = agdrschema.getRootNode() # only one project node

        self._relateSchemas() # build graph structure

    def _relateSchemas(self):
        '''
        connect nodes from the agdrschema, e.g. nodes to their 
        parents and children

        it's not only about the dictionary structure, but also 
        matching the correct parent/child submitter ids
        '''
        # TODO: change to logger.debug when done
        logger.warn(f"root: {self._root.getGen3NodeName()}")
        logger.warn("parents:")
        logger.warn(f"\t {[x.name for x in self._root.getGen3Node().getParents()]}")
        logger.warn("children:")
        logger.warn(f"\t {[x.name for x in self._root.getGen3Node().getChildren()]}")

    def getRootNode(self):
        '''
        return the root node of the agdr schema. This is the 
        metadata-containing schema
        '''
        pass

    def walk(self):
        '''
        walk the graph structure, for only nodes containing metadata
        '''
        pass

    def validate(self):
        '''
        - schema level   -- check if the graph structure is valid 
          (each node has expected nodes and children)
        - node   level   -- check that each node has required properties 
        - property level -- check that each property is valid
        '''
        pass