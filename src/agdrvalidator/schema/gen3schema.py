'''
@Author: Eirian Perkins

This file provides a concrete implementation of a Schema, which is 
composed of Nodes. The Gen3 Schema implementation should be able to
parse an arbitrary Gen3 dictionary structure and should not need to 
be updated for specific versions of a metadata structure apart from 
resolving any bugs identified.
'''
from agdrvalidator.utils import logger
from agdrvalidator.schema.base import *

logger = logger.setUp(__name__)

class Gen3(Schema):
    def __init__(self, root=None):
        self._root = root

        self._definitions = None
        self._settings = None
        self._terms = None

        self.nodes = {}


    def setRoot(self, root):
        self._root = root

    def setDefinitions(self, defs):
        self._definitions = defs

    def setSettings(self, sets):
        self._settings = sets

    def setTerms(self, terms):
        self._terms = terms

    
    def getUploadOrder(self):
        '''
        Determine upload order required for Gen3 so that metadata nodes 
        can be ingested from the root node down to the leaves.
        '''
        visitedNodes = set()
        # walk from root to leaves
        # only yield node if all parents have been visited
        def bfsInOrder(node):
            parents = [x.name for x in node.getParents()]
            visited = [x.name for x in visitedNodes]
            if set(parents).issubset(set(visited)):
                if node.name not in visited:
                    visitedNodes.add(node)
                    yield node
            if node.getChildren():
                for child in node.getChildren():
                    if child.name in visitedNodes:
                        continue
                    yield from bfsInOrder(child)

        orderedNodes = []
        for node in bfsInOrder(self._root):
            orderedNodes.append(node)
        return orderedNodes

    def walk(self, revisitNodes=False):
        for node in self.getUploadOrder():
            yield node
