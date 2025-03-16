'''
This file provides the base class for all TSV transformers, which 
convert a specific metadata structure into a collection of TSV files.
When a new data dictionary structure is created, a new TSV transformer
subclass should be implemented rather than refactoring the existing
transformers. This is to ensure that the existing transformers are
not broken by changes to the new data dictionary structure, contributing 
to the maintainability of the codebase and the ability to implement 
backwards compatibility with older metadata structures.
'''
import abc


class TSVTransformer(abc.ABC):
    def __init__(self, node):
        self._node = node

    @abc.abstractmethod
    def toTSV(self, outputdir=None):
        pass
