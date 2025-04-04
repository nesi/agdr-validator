'''
This file provides the base class for all nodes in the schema. Using 
the abstract base class design pattern ensures that all Node 
subclasses have the same interface, which lowers cognitive complexity
and encourages object-oriented design principles.
'''
import abc


class Node(abc.ABC):
    def __init__(self):
        self._properties = []
        self._parents = []
        self._children = []

    @abc.abstractmethod 
    def walk(self):
        pass

    @abc.abstractmethod 
    def isParent(self, node_id):
        pass

    @abc.abstractmethod 
    def getParents(self):
        pass

    @abc.abstractmethod 
    def getChildren(self):
        pass

    @abc.abstractmethod 
    def addParent(self, parent):
        pass

    @abc.abstractmethod 
    def addChild(self, child):
        pass