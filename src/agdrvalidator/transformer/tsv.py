import abc

class TSVTransformer(abc.ABC):
    def __init__(self, node):
        self._node = node

    @abc.abstractmethod
    def toTSV(self, outputdir=None):
        pass
