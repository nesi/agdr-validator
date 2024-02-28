'''
@Author: Eirian Perkins

This file provides some helper functions for the agdrvalidator package.
'''
import re
from datetime import datetime
import dateutil.parser as dp

def boolify(value):
    # for use in TSV generation
    falsy = ['false', 'f', 'no', 'n', '0']
    if not value:
        return "false"
    elif str(value).lower() in falsy:
        return "false"
    else:
        return "true"


def latlonify(value):
    # for use in TSV generation
    if not value:
        return "0", "0"
    if "," in value:
        lat, lon = value.split(",")
        lat = lat.strip()
        lon = lon.strip()
        return lat, lon

    # DMS: conversion to decimal
    # D + M/60 + S/3600
    # S may not be included
    # AGDR actually asks for decimal degrees,
    # this is why we do not do the conversion here
    # (assume it is all decimal input, not DMS)

    N = re.search(r"(\d+\.\d+)(\s+)?[Nn]", value)
    S = re.search(r"(\d+\.\d+)(\s+)?[Ss]", value)
    E = re.search(r"(\d+\.\d+)(\s+)?[Ee]", value)
    W = re.search(r"(\d+\.\d+)(\s+)?[Ww]", value)

    if N:
        lat = N.group(1)
    elif S:
        lat = "-" + S.group(1)
    else:
        return "0", "0"
    if E:
        lon = E.group(1)
    elif W:
        lon = "-" + W.group(1)
    else:
        return "0", "0"
    
    #print(f"{value} -> {lat}, {lon}")
    return lat, lon


def dateify(value):
    if not value:
        return "null"
    sval = str(value)
    if sval.lower() == "unknown":
        return "null"
    
    result = "null"
    try:
        result = value.strftime('%b-%Y')
    except:
        result = dp.parse(sval).strftime('%b-%Y')
    return result