import abc
# abc.ABC vs abc.ABCMeta
# https://stackoverflow.com/questions/33335005/is-there-any-difference-between-using-abc-vs-abcmeta

class Parser(abc.ABC):
    def __init__(self, datapath):
        self.datapath = datapath

    @abc.abstractmethod 
    def parse(self):
        pass