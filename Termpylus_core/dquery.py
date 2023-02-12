# Querying nested dicts.
#Look for weighted combination of keywords, uses, etc.
from Termpylus_shell import pybashlib
from . import dwalk # TODO: use this.

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

def fn_arity_metric(sym_qual, arity):
    #https://stackoverflow.com/questions/990016/how-to-find-out-the-arity-of-a-method-in-python
    inspect.getargspec(fn_obj)
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

def fcallcount_gmetric(query):
    # How many times were the fns used?
    # Requires the functions to be watched to be nonzero.
    TODO

########################Putting it all together#################################

def generic_find(bashy_args, query_target):
    # Weight these metrics together, and find the symbols.
    def m2g(module_level_f): # Global fns only input a query.
        return None
        TODO
    def l2g(local_level_f):
        return None
        TODO
    wts = {'-n':['Fn name, qualified by module', l2g(fnname_metric)],
           '--ar':['Fn arity, variable arity has partial match', l2g(fn_arity_metric)],
           '-s':['Source code text-match.', m2g(source_mmetric)],
           '--sr':['Source code text-match, regexp only (useful when entering as a bash cmd).', lambda q: m2g(source_mmetric)(Regexp(q))],
           '-i':['Function inputs match. Requires watchers to be set up. May skim over very large datasets.', m2g(fninputs_gmetric)],
           '-o':['Function output match. Requires watchers to be set up. May skim over very large datasets.', m2g(fninputs_gmetric)],
           '--ncall':['Function call count. Requires watchers to be set up.', m2g(fninputs_gmetric)]
           }
    if len(bashy_args)==0: # Help mode.
        out = 'Search through python defs at module level or class level. Will search nested classes but'
        out = out+' The search sorts by the top results. Querys can be string or object. The following search criteria are allowed:'
        kys = list(wts.keys()); kys.sort()
        for k in kys:
            out = out+'\n'+k+': '+str(wts[k][0])
        out = out+'\n'+'Examples: "pfind -n xyz.foo -s bar" will look for a "def foo:" in module xyz with bar in its source code.'
        out = out+'\n'+'"pfind -n6 abc -i2 xyz --num3 ikl" will apply 6:3:2 weights.'
        return out

    P = pybashlib.option_parse(args, []); fl = set(P['flags']); kv = P['pairs']; x = P['tail']
    print('Bashy args:', bashy_args)
    TODO
    TODO # --sr option.