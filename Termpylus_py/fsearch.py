# Search for function definitions.

'''

Look for  weighted combination of keywords, uses, weights, etc.

'''

##########################Lower-level fns#############################

class Regexp():
    #String literal that signales leaf_match to use regexp matching.
    def __init__(self, val):
        self.val = val
    def __str__(self):
        return self.val

def leaf_match(x, query):
    # Matches are zero to 1.
    # Flexible as to what the function matches.
    if query==x or query is x:
        return 1.0

    if type(query) is str:
        # Simple str matching.
        TODO
    elif type(query) is Regexp:
        # Match regexp.
        TODO
    elif callable(query):
        TODO
    else:
        return leaf_match(x, str(query))

##########################Walking fns#############################

def to_dict(x, blockset):
    # Converts something to x. Blockset blocks circular references.
    TODO

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
    # Matches dict keys to query. Operates recursively.
    TODO

def v_match(x, query, blocklist=None):
    # look for these dict values. Operates recursively.
    TODO

########################Search metrics, individual##############################

def fnname_metric(sym_qual, query):
    # These metric functions match query (a string, function, or target object) to sym_qual.
    # 0 is no match at all and 1 is a perfect match.
    # This matches the function to the qualified name of the symbol.
    TODO

########################Search metrics, module level##############################

def source_mmetric(mname, argf):
    # Text-based matches to the source code. Naive to the syntax.
    # Module-level metrics and global-level metrics return a dict from the qualed name to the score.
    TODO

########################Search metrics, across all functions##############################

def fninputs_gmetric(query):
    # Matches against inputs to the function.
    # Requires the function to be watched to be nonzero.
    TODO

def fnreturn_gmetric(query):
    # Matches against inputs to the function.
    # Requires the functions to be watched to be nonzero.
    TODO

def fcallcount_gmetric():
    # How many times were the fns used?
    # Requires the functions to be watched to be nonzero.
    TODO

########################Putting it all together#################################

def generic_find(arg_map):
    # Weight these metrics together, and find the symbols.
    TODO
