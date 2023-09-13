import json 
import math

def pprintj(jdata=None):
    # pretty print json
    print(json.dumps(jdata, indent=4))


def is_nan(foo):
    if type(foo) == int or type(foo) == float:
        if math.isnan(foo):
            return True 
    return False
