from agdrvalidator.utils import logger
from agdrvalidator.schema import *

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

    
    def walk_thoughts(self):
        #pass

        def dfs(node, level=0):
            if node.getChildren():
                return dfs(node.walk(), level=level+1)
            return (node,level)

        nodes = []
        curr = self._root 
        level = 0
        for node in curr.walk():
            indent = '\t'*level
            print(f"{indent}{node}")
            ####
            nodes.append(dfs(node))
        # probably want to sort nodes in term of level 
        # and then print with indentations
        # that's not what I want to do, that would lose the parent node
        # I want to print the parent node and then the children
        # so how do I do that recursively
        return nodes


    def getUploadOrder(self):
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
