# Querying nested dicts.
# Some functions are generic while others are specalized to searching through source, etc.
#Look for weighted combination of keywords, uses, etc.
import numpy as np
from . import dwalk
from Termpylus_shell import bash_helpers

def leaf_match(x, query):
    # Matches are zero to 1.
    # Flexible as to what the function matches.
    if query==x or query is x:
        return 1.0

    if type(query) is str:
        # Simple str matching.
        return bash_helpers.flex_match(query, x, gradation=True)
    elif type(query) is Regexp:
        # Match regexp.
        return query.match_score(x)
    elif callable(query):
        return query(x)
    else:
        return leaf_match(str(x), str(query))

def sum_combine(kvs):
    out = 0
    for v in kvs.values():
        if v is None:
            continue
        out = out+v
    return out

def max_combine(kvs):
    out = 0
    for v in kvs.values():
        if v is None:
            continue
        out = max(out,v)
    return out

def sort_by(x, scores):
    # Returns x sorted by lowest to highest score.
    pairs = [[x[i], scores[i]] for i in range(len(x))]
    #https://docs.python.org/3/howto/sorting.html
    pairs1 = sorted(pairs, key=lambda pair: pair[1])
    return [pair[0] for pair in pairs1]

def k_or_v_match(x, query, is_v, blocklist=None):
    # Matches dict keys or values to query. Operates recursively.
    blocklist = set() if blocklist is None else set(blocklist)
    match = 0.0
    for k in x.keys():
        if k in blocklist:
            continue
        if type(x) is dict:
            match = max(match, k_or_v_match(x[k], query, is_v, blocklist))
        else:
            match = max(match, leaf_match(x[k] if is_v else k, query))
    return match
