'''
@Author: Eirian Perkins

Base class for properties. Each node has a collection of properties, 
and a collection of nodes makes a schema.

Ideally this should be in some base.py file
'''
import abc

class Property(abc.ABC):
    def __init__(self, name, value=None):
        self._input_name = name
        self._name = name
        self._value = value

    def get_name(self):
        return self._name

    def get_value(self):
        return self._value