# Search for function definitions.

'''

Look for  weighted combination of keywords, uses, weights, etc.

'''

##########################Lower-level fns#############################

def owalk(x, eval_f, combine_f, blockset, eval_kys=False):
    # Walk through data structures to find something.
    # Runs eval f and combines results with combine_f (which always gets a dict).
    y = {None, eval_f(x)}
    kvs = {}
    if has_attr(x, '__dict__'):
        TODO
    elif type(x) is dict:
        TODO
    elif type(x) is list:
        TODO
    elif type(x) is set:
        TODO

    ys = {}
    for k in kvs.keys():
        v = kvs[k]
        if v in blockset:
            TODO
        else:
            blockset.add(v)
    TODO

def sum_combine(kvs):
    TODO

def max_combine(kvs):
    TODO

##############################Match functions##############################

def k_match(x, query, blocklist=None):
    # Matches dick keys to query. Operates recursively.

    TODO

def v_match(x, query, blocklist=None):
    # look for these dict values. Operates recursively.
    TODO

##############################Metrics of functions##############################

def name2source(sym_qual):
    # Gets the source code txt.
    TODO
    return txt, where

def name_metric(sym_qual, query):
    TODO

def input_metric(sym_qual, argf):
    # How much do we match an input?
    TODO

def generic_find(args):
    TODO
