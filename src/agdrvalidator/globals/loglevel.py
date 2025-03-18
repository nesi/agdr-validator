'''
A little module to set the log level for the entire package.

Note that if you add imports in __main__.py before init() is called,
setting the loglevel, then the log level will default to ERROR 
for those imported modules.
'''
import logging

LOGLEVEL = logging.ERROR

def init(level):
    global LOGLEVEL
    LOGLEVEL = level