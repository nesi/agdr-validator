'''
this file contains data container classes used to represent 
metadata from excel workbook input.
'''

from openpyxl.utils import get_column_letter


class CellLocation(object):
    '''
    this class represents the coordinates for a particular cell

    a string representation will give the cell name instead of 
    x, y coordinates, e.g. 'A1' rather than (0, 0)
    '''
    def __init__(self, row, column):
        self.row = row
        self.column = column

    def __str__(self):
        if self.row is None or self.column is None:
            return "N/A"
        col_letter = get_column_letter(self.column)
        return f"{col_letter}{self.row}"
    
    def __repr__(self):
        return self.__str__()

    def __bool__(self):
        return self.row is not None and self.column is not None

class SpreadsheetProperty(object):
    '''
    This class represents data for a single cell, including 
    the header name (self.name) and value (self.data).

    If the SpreadsheetProperty has no data, then it represents a 
    header cell
    '''
    def __init__(self, name, value, cell_location:CellLocation, required=False):
        self.name = name
        self.data = value
        self.location = cell_location
        self.required = required

    def __str__(self):
        return f"Name: {self.name}, Value: {self.data}, Location: ({self.location}), Required: {self.required}"

    def __repr__(self):
        return f"SpreadsheetProperty(name={self.name}, value={self.data}, cell_location=CellLocation({self.location}), required={self.required})"

class SpreadsheetRow(object):
    '''
    This class represents an entire row of data from a 
    table in the spreadsheet input
    '''
    def __init__(self, properties: list[SpreadsheetProperty], sheet_name):
        self.data = properties # list of SpreadsheetProperty objects
        self.sheet_name = sheet_name
        self.headers = None # to be set later

    def __getitem__(self, index):
        return self.data[index]

    def __str__(self):
        return f"SpreadsheetRow(data={self.data})"

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        # iterate over properties
        return iter(self.data)

    def get(self, key):
        # retrieve a property
        for prop in self.data:
            if key.lower() == str(prop.name).lower():
                return prop
        return None
class SpreadsheetNode(object):
    '''
    This class represents all rows of data for a particular 
    node type, such as Project, Dataset, or File metadata.

    self.name represents the table name
    '''
    def __init__(self, name, data=[]):
        self.name = name
        self.data: list[SpreadsheetRow] = data

    def __str__(self):
        if not self.data:
            return f"SpreadsheetNode(name={self.name}, data=[])"
        rows_str = "\n\t".join([str(row) for row in self.data])
        return f"SpreadsheetNode(name={self.name}, data=[\n\t{rows_str}\n])" 

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        # iterate over rows
        return iter(self.data)

    def update(self, other):
        # update data with data from other
        self.data.extend(other.data)