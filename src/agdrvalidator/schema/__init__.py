import abc

class Schema(abc.ABC):
    def __init__(self, root):
        self._root = root

    def getRootNode(self):
        return self._root

    @abc.abstractmethod 
    def walk(self):
        pass