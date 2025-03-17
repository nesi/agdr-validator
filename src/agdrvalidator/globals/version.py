'''
This file provides the version of the package, in the format:
    major.minor.spreadsheetVersion.agdrDictionaryVersion
'''

def version(spreadsheet=None):
    if not spreadsheet:
        spreadsheet = "unknown"
    nesi_version = f"1.2.{spreadsheet}.2025_01_24"
    return nesi_version
