'''
This file provides some basic Exceptions for the agdrvalidator package.
'''
class AgdrFormatException(Exception):
    pass

class AgdrImplementationException(Exception):
    pass

class AgdrNotFoundException(Exception):
    pass

class BadMetadataSpreadsheetException(Exception):
    pass

class AgdrNotImplementedException(Exception):
    pass