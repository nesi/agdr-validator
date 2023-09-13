# TODO: delete this file

#from agdrvalidator.utils import logger
from agdrvalidator.schema.node import *

#logger = logger.setUp(__name__)

class Multiplicity():
    def __init__(self):
        pass

class TemplateNode(Node):
    def __init__(self):
        super().__init__()

    @abc.abstractmethod 
    def walk(self):
        pass

    @abc.abstractmethod 
    def getParents(self):
        pass

    @abc.abstractmethod 
    def getChildren(self):
        pass

    @abc.abstractmethod 
    def addParent(self, parent, multiplicity=None):
        pass

    @abc.abstractmethod 
    def addChild(self, child, multiplicity=None):
        pass