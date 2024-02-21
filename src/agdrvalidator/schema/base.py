'''
@Author: Eirian Perkins

This file provides an abstract base class for a Schema, which is the 
structure that holds a collection of nodes, which are composed of 
properties. The base classes have the logic to walk through a dictionary 
structure and connect nodes to each other in parent-child relationships.
'''
import abc

class Schema(abc.ABC):
    def __init__(self, root):
        self._root = root

    def getRootNode(self):
        return self._root

    @abc.abstractmethod 
    def walk(self):
        pass