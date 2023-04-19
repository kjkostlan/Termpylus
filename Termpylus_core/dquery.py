# Querying nested dicts.
# SOme functions are generic while others are specalized to searching through source, etc.
#Look for weighted combination of keywords, uses, etc.
import re, inspect
import numpy as np
from . import dwalk, file_io, var_watch
from Termpylus_lang import pyparse, modules, ppatch
from Termpylus_shell import bash_helpers

##########################Lower-level fns#############################

class Regexp():
    #String literal that signales leaf_match to use regexp matching.
    def __init__(self, val):
        self.val = val
    def __str__(self):
        return self.val
    def match_score(self, txt):
        if re.match(self.val, txt) is not None:
            return 1.0
        return 0.0

def str_str_match(x, query):
    # Simple string string match. Ways to improve partial matches TODO:
    #  Spell check.
    #  Thesaouros/word vector distances.
    #  Underscores vs CamelCase vs etc.
    #  ...
    if str(x)==str(query):
        return 1.0
    if str(x).lower()==str(query).lower():
        return 0.75
    if str(x).lower() in str(query).lower():
        return 0.5
    if str(query).lower() in str(x).lower():
        return 0.5
    return 0.0

def leaf_match(x, query):
    # Matches are zero to 1.
    # Flexible as to what the function matches.
    if query==x or query is x:
        return 1.0

    if type(query) is str:
        # Simple str matching.
        return str_str_match(x, query)
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

def _peak(target, val):
    if target==0:
        return float(target==val)
    diff = float(target-val)
    return float(target)*target/(target*target+diff*diff)

##############################Recursive matching################################

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

################################################################################
########################Searching the code and modules##########################

class Sourcevar:
    # Source variable that we pass to the metric functions.
    def __init__(self, modulename, varname, src_txt0, src_txt1, src_datemod):
        logss = var_watch.get_logs()
        self.is_ppatched = ppatch.is_modified(modulename, varname)
        self.logs = logss.get(modulename+'.'+varname, [])
        self.modulename = modulename
        self.varname = varname
        self.src_txt = src_txt1 # Txt of the function body.
        src_edit = pyparse.txt_edit(src_txt0, src_txt1)
        self.src_edit = src_edit # Edit on the fn body since program startup.
        self.src_datemod = src_datemod
        self.signature = None
        self.score = None
        try:
            f = ppatch.get_var(modulename, varname)
        except AttributeError:
            f = None
        if f is not None:
            try:
                self.signature = inspect.signature(f)
            except Exception as e:
                raise Exception(f'signature error on {modulename}.{varname}: {e}')

    def __str__(self):
        log_score = self.is_ppatched*8+len(self.logs)
        log_txt = ''
        if self.is_ppatched:
            log_txt = ' 👁'
        if len(self.logs)>0:
            log_txt = log_txt+' '+str(len(self.logs))
        return 'Ͼ'+self.modulename+'.'+self.varname+log_txt+'Ͽ'

    def __repr__(self):
        return 'Sourcevar('+str(self)+')'

####### Metrics that return 0 (no match) through 1 (perfect match) #############

def fnname_metric(sourcevar, query):
    # Matches the function to the qualified name of the symbol.
    #print('Fn name match:', sourcevar.modulename+sourcevar.varname, query, str_str_match(sourcevar.modulename+sourcevar.varname, query))
    return str_str_match(sourcevar.modulename+sourcevar.varname, query)

def fn_arity_metric(sourcevar, query):
    # Includes optional args.
    if sourcevar.signature is None:
        return False
    arity = len(str(sourcevar.signature).split(','))
    return _peak(int(query), arity)

def source_metric(sourcevar, query):
    # Text-based matches to the source code. Naive to the syntax.
    # Module-level metrics and global-level metrics return a dict from the qualed name to the score.
    return str_str_match(sourcevar.src_txt, query)

def source_edit_metric(sourcevar, query=None):
    # How much has the source been edited?
    txt = sourcevar.src_txt; ed = sourcevar.src_edit
    if ed is None:
        return 0.0
    ed_sz = 0.5*(len(ed[2])+len(ed[3]))
    src_sz = len(txt)+1
    return min(ed_sz/src_sz, 1.0)

def fninputs_metric(sourcevar, query):
    # Matches against inputs to the function.
    # Requires the function to be watched to be nonzero.
    if len(self.logs)==0: #self.logs is [log ix][k] => v.
        return 0.0
    inputss = []
    for lg in self.logs:
        x = lg.copy(); del x['return']; del x['_time']
        inputss.append(x)
    total_score = np.sum([k_or_v_match(inputs, query, True) for inputs in inputss])
    return min(1.0, total_score/len(self.logs))

def fnreturn_metric(sourcevar, query):
    # Matches against inputs to the function.
    # Requires the functions to be watched to be nonzero.
    if len(self.logs)==0:
        return 0.0
    returns = [x['return'] for x in self.logs]
    total_score = np.sum([leaf_match(ret, query, True) for ret in returns])
    return min(1.0, total_score/len(self.logs))

def fcallcount_metric(sourcevar, query):
    # How many times were the fns used?
    # Requires the functions to have logs to be non-zero.
    return _peak(int(query), len(sourcevar.logs))

def usecount_metric(sourcevar, query, sourcevars_precompute=None):
    if sourcevars_precompute is None:
        sourcevars_precompute, _ = get_all_sourcevars()
    leaf = sourcevar.varname.split('.')[-1] # TODO: Not just use leafs.
    n = 0
    for sv in sourcevars_precompute:
        if leaf in sv.src_txt:
            n = n+1

    return _peak(int(query), n)

########################Putting it all together#################################

def get_all_sourcevars():
    # List of sourcevars and tokens in the source.
    out = []
    fnames = modules.module_fnames(user_only=True)
    src_token_counts = {}
    for k in fnames.keys():
        contents = file_io.contents(fnames[k]); date_mod = file_io.date_mod(fnames[k])
        contents0 = file_io.contents_on_first_call(fnames[k])
        src_pieces = pyparse.simple_tokens(contents)
        for p in src_pieces:
            src_token_counts[p] = src_token_counts.get(p,0)+1
        defs = pyparse.sourcecode_defs(contents, nest=True)
        defs0 = pyparse.sourcecode_defs(contents0, nest=True)
        for dk in defs.keys():
            out.append(Sourcevar(k, dk, defs0.get(dk,''), defs[dk], date_mod))
    return out, src_token_counts

def source_find(*bashy_args):
    all_src_vars, src_token_counts = get_all_sourcevars()

    def use_count(sourcevar, query):
        return usecount_metric(sourcevar, query, src_token_counts)

    verbose_key = '-v'

    # Weight these metrics together, and find the symbols.
    fns = {'-n':['Fn name, can be qualified by module', fnname_metric],
           '-ar':['Fn arity, variable arity has partial match', fn_arity_metric],
           '-s':['Source code text-match.', source_metric],
           '-se':['Edits to this fn in the source code.', source_edit_metric],
           '-u':['Uses of the leaf name in all the source texts.', use_count],
           '-sr':['Source code text-match, regexp only (useful when entering as a bash cmd).', lambda q: source_metric(Regexp(q))],
           '-i':['Function inputs match. Requires watchers to be set up. May skim over very large datasets.', fninputs_metric],
           '-o':['Function output match. Requires watchers to be set up. May skim over very large datasets.', fnreturn_metric],
           '-ncall':['Function call count. Requires watchers to be set up.', fninputs_metric]}
    if len(bashy_args)==0: # Help mode.
        out = 'Search through python defs at module level or class level. Includes defs in classes.'
        out = out+' The search returns the top results. Querys can be string or object. The following search criteria are allowed:'
        kys = list(fns.keys()); kys.sort()
        for k in kys:
            out = out+'\n'+k+': '+str(fns[k][0])
        out = out+'\n'+'Examples: "sfind -n xyz.foo -s bar" will look for a "def foo:" in module xyz with bar in its source code.'
        out = out+'\n'+'"sfind -n6 abc -i2 xyz -num3 ikl" will apply 6:3:2 weights.'
        out = out+'\n'+'Use '+verbose_key+' to output a more comprehensive dataset for further processing.'
        return out

    P = bash_helpers.option_parse(bashy_args, fns.keys()); fl = set(P['flags']); kv = P['pairs']; x = P['tail']

    # Calculated weighed sum:
    triplets = []
    for opt in kv.keys():
        wt = re.sub(r"\D", '', opt)
        wt = 1 if wt=='' else int(wt)
        fn = fns[re.sub(r"\d", '', opt)][1]
        triplets.append([wt, fn, kv[opt]])

    #print('tail is:', x, 'fl is:', fl, 'kv is:', kv)
    verbose_mode = verbose_key in fl

    # Sum up weights step:
    src_vars = []
    N = len(all_src_vars)
    for i in range(N):
        sc = 0
        for t in triplets:
            sc = sc+t[0]*t[1](all_src_vars[i], t[2])
        if sc>0 or verbose_mode: # At least some match.
            all_src_vars[i].score = sc
            src_vars.append(all_src_vars[i])
    src_vars_hi2low = sort_by(src_vars, [-sv.score for sv in src_vars])

    if verbose_key in fl:
        return src_vars_hi2low
    else:
        n_return = min(len(src_vars_hi2low), 8) # How many results to show.
        return [x.modulename+'.'+x.varname for x in src_vars_hi2low[0:n_return]]
