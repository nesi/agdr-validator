'''
Simple data container for excel metadata, used for the 
original version of the agdrvalidator 

this is now deprecated, use rich_tabular.py instead
'''
class Table():
    def __init__(self):
        self.header = []
        self.required = []
        self.data = []

    def get(self, item):
        idx = self.header[0].index(item)
        return [row[idx] for row in self.data]

    def getIndexOf(self, item):
        return self.header[0].index(item)