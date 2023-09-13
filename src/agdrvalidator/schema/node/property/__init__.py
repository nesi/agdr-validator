import abc

class Property(abc.ABC):
    def __init__(self, name, value=None):
        self._name = name
        self._value = value

    def get_name(self):
        return self._name