import pandas as pd 

def chomp(arr):
    x = -1
    for i in range(len(arr)):
        if pd.notna(arr[x]):
            break
        else:
            x -= 1
    if x == -1:
        return arr
    else:
        return arr[:x+1]


def chomp_front(arr):
    x = 0
    for i in range(len(arr)):
        if pd.notna(arr[x]):
            break
        else:
            x += 1
    if x == 0:
        return arr
    else:
        return arr[x:]


