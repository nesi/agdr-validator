'''
This file provides a function to set up a logger for the package.

A class is useful for setting up formatting and handlers for the logger.
It should be created per-module so that the module name and line number
are included in the log messages.
'''
import logging

import agdrvalidator.globals.loglevel as logsettings


def setUp(name):
    logger = logging.getLogger(name)
    logger.setLevel(logsettings.LOGLEVEL)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(lineno)d: %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger