# Metrics to determine how much a variable matches a field.
import re, inspect
from Termpylus_extern.fastatine import python_parse
from Termpylus_extern.waterworks import file_io, modules, fittings, var_watch, ppatch
from Termpylus_core import dquery
from Termpylus_shell import bash_helpers
import proj

class Sourcevar:
    # A fair amount of information about a source's variable.
    def __init__(self, modulename, varname, src_txt0, src_txt1, src_datemod):
        self.is_ppatched = ppatch.is_modified(modulename, varname)
        self.logs = var_watch.get_logs(modulename, varname)
        self.modulename = modulename
        self.varname = varname
        self.src_txt_old = src_txt0
        self.src_txt = src_txt1 # Txt of the function body.
        self.src_edits = fittings.txt_edits(src_txt0, src_txt1) # Edit on the fn body since program startup.
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
                if 'is not a callable object' in str(e) or 'no signature found for builtin type' in str(e):
                    pass # For these it's fine to keep signature as None.
                else:
                    raise Exception(f'Strange signature error on {modulename}.{varname}: {e}')

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

def _peak(target, val):
    if target==0:
        return float(target==val)
    diff = float(target-val)
    return float(target)*target/(target*target+diff*diff)

def fnname_metric(sourcevar, query):
    # Matches the function to the qualified name of the symbol.
    return bash_helpers.flex_match(query, sourcevar.modulename+sourcevar.varname)

def fn_arity_metric(sourcevar, query):
    # Includes optional args.
    if sourcevar.signature is None:
        return False
    arity = len(str(sourcevar.signature).split(','))
    return _peak(int(query), arity)

def source_metric(sourcevar, query):
    # Text-based matches to the source code. Naive to the syntax.
    # Module-level metrics and global-level metrics return a dict from the qualed name to the score.
    return bash_helpers.flex_match(query, sourcevar.src_txt)

def single_edit_wt(txt, ed):
    # How much edit is this edit?
    # TODO: new or deleted vars should be heavilly edited.
    query = float(query)
    if ed is None or ed == [0,0,'','']:
        return 0.0
    else:
        ed_sz = 0.5*(ed[1]-ed[0]+len(ed[2]))
        src_sz = len(txt)+1
        return ed_sz/src_sz
    return 0.0

def source_edit_metric(sourcevar, query):
    # Are you searching for heavily-edited or lightly-edited vars?
    query = float(query)
    txt = sourcevar.src_txt; eds = sourcevar.src_edits
    wt = 0
    for ed in eds:
        wt = wt + single_edit_wt(txt, ed)
    if wt > 1.0:
        wt = 1.0
    score = 1.0-abs(query-wt)
    if score < 0:
        score = 0
    return score

def fninputs_metric(sourcevar, query):
    # Matches against inputs to the function.
    # Requires the function to be watched to be nonzero.
    if len(self.logs)==0: #self.logs is [log ix][k] => v.
        return 0.0
    inputss = []
    for lg in self.logs:
        x = lg.copy(); del x['return']; del x['_time']
        inputss.append(x)
    total_score = np.sum([dquery.k_or_v_match(inputs, query, True) for inputs in inputss])
    return min(1.0, total_score/len(self.logs))

def fnreturn_metric(sourcevar, query):
    # Matches against inputs to the function.
    # Requires the functions to be watched to be nonzero.
    if len(self.logs)==0:
        return 0.0
    returns = [x['return'] for x in self.logs]
    total_score = np.sum([dquery.leaf_match(ret, query, True) for ret in returns])
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
        contents = file_io.fload(fnames[k]); date_mod = file_io.date_mod(fnames[k])
        contents0 = file_io.contents_on_first_call(fnames[k])
        src_pieces = python_parse.simple_tokens(contents)
        for p in src_pieces:
            src_token_counts[p] = src_token_counts.get(p,0)+1
        defs = python_parse.sourcecode_defs(contents, nest=True)
        defs0 = python_parse.sourcecode_defs(contents0, nest=True)
        for dk in defs.keys():
            out.append(Sourcevar(k, dk, defs0.get(dk,''), defs[dk], date_mod))
    return out, src_token_counts

def source_find(*bashy_args):

    verbose = 12; shall = '-showall'; k_return_sv = '-returnsrcv'; pkp = '-precompute'
    opts = {shall:f'Set the max number of results returned; default is {verbose}',
            '-f':'User fn takes in the sourcevar.',
            k_return_sv:'Return the source var object instead of just the name.',
            pkp:'Reuse all_src_vars from the last (useful for large projects).'}

    if len(bashy_args) %2 != 0:
        raise Exception('Args must be in pairs of -key query -key query ...')

    i = 0
    all_src_vars = None
    while i<len(bashy_args):
        ky = str(bashy_args[i]).lower(); query = bashy_args[i+1]
        if ky==pkp and bool(query) and 'dquery_globals' in proj.dataset and 'src_vars' in proj.dataset['dquery_globals']:
            all_src_vars = proj.dataset['dquery_globals']['src_vars']
        i = i+2
    if all_src_vars is None:
        all_src_vars, _ = get_all_sourcevars()
        proj.dataset['dquery_globals'] = {'src_vars':all_src_vars}
    def use_count(sourcevar, query): # Avoid recalculating all_src_vars for each src_var.
        return usecount_metric(sourcevar, query, all_src_vars)

    # Weight these metrics together, and find the symbols.
    fns = {'-n':['Fn name, can be qualified by module', fnname_metric],
           '-ar':['Fn arity, variable arity has partial match', fn_arity_metric],
           '-s':['Source code text-match.', source_metric],
           '-ed':['Edits to this fn in the source code.', source_edit_metric],
           '-u':['Uses of the leaf name in all the source texts.', use_count],
           '-i':['Function inputs match. Requires watchers to be set up. May skim over very large datasets.', fninputs_metric],
           '-o':['Function output match. Requires watchers to be set up. May skim over very large datasets.', fnreturn_metric],
           '-ncall':['Function call count. Requires watchers to be set up.', fcallcount_metric]}

    if len(bashy_args)==0: # Help mode.
        out = 'Search through python defs at module level or class level. Includes defs in classes.'
        out = out+' The search returns the top results. Querys can be string or object. The following search criteria are allowed:'
        for kys in [fns.keys(), opts.keys()]:
            kys = list(fns.keys()); kys.sort()
            for k in kys:
                out = out+'\n'+k+': '+str({**fns,**opts}[k][0])
        kys = list(fns.keys()); kys.sort()
        for k in kys:
            out = out+'\n'+k+': '+str(fns[k][0])
        out = out+'\n'+'Examples: "sfind -n xyz.foo -s bar" will look for a "def foo:" in module xyz with bar in its source code.'
        out = out+'\n'+'"sfind -n6 abc -i2 xyz --num3 ikl" will apply 6:2:-3 weights (-- = negative wt). Ints only.'
        return out

    i = 0
    weights = {}; return_sv = False
    for sv in all_src_vars:
        sv.score = 0.0
    while i<len(bashy_args):
        ky = str(bashy_args[i]).lower(); query = bashy_args[i+1]
        wt = re.sub(r"\D", '', ky)
        wt = 1 if wt=='' else int(wt)
        if ky.startswith('--'):
            wt = -wt
        ky = re.sub(r"\d", '', ky.replace('--','-'))
        if ky==shall:
            verbose = int(query)
        elif ky==k_return_sv:
            return_sv = bool(query)
        elif ky=='-f':
            for sv in all_src_vars:
                sv.score = sv.score+query(sv)
        elif ky not in fns and ky not in opts:
            raise Exception('Unrecognized option:'+ky)
        elif ky in fns:
            f = fns[ky][1]
            for sv in all_src_vars:
                add_score = f(sv, query)*wt
                sv.score = sv.score+add_score
        i = i+2

    src_vars_hi2low = dquery.sort_by(all_src_vars, [-sv.score for sv in all_src_vars])

    n_return = min(len(src_vars_hi2low), verbose) # How many results to show.
    if return_sv:
        return src_vars_hi2low[0:n_return]
    return [x.modulename+'.'+x.varname for x in src_vars_hi2low[0:n_return]]

def pythonverse_find(*bashy_args, pythonverse_verse=None, exclude_Termpylus=False):
    # Similar to source find, but over the Pythonverse.
    TODO
