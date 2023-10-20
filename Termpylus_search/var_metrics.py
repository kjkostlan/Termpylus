# Metrics to determine how much a variable matches a field.
import re, inspect, time
from Termpylus_extern.fastatine import python_parse
from Termpylus_extern.waterworks import file_io, modules, fittings, var_watch, ppatch, py_updater
from Termpylus_core import dquery
from Termpylus_shell import bash_helpers
import proj

class Sourcevar:
    # A fair amount of information about a source's variable.
    def __init__(self, filename, varname_full, src_txt0, src_txt1, src_datemod):
        self.has_module = not varname_full.startswith('FILE:')
        self.is_ppatched = ppatch.is_modified(varname_full) if self.has_module else None
        self.logs = var_watch.get_logs(varname_full) if self.has_module else []
        self.filename = filename
        self.varname_full = varname_full
        self.src_txt_old = src_txt0
        self.src_txt = src_txt1 # Txt of the function body.
        self.src_edits = fittings.txt_edits(src_txt0, src_txt1) # Edit on the fn body since program startup.
        self.src_datemod = src_datemod
        self.arglist = None # Similar to a signature, but simply an array of string appearing as-is.
        self.score = None

        only_use_python_parse = True
        if not only_use_python_parse: # Option to use inspect, but it will not work if the
            sig = None
            try:
                f = ppatch.get_var(varname_full) if self.has_module else None
            except AttributeError:
                f = None
            if f is not None:
                try:
                    sig = str(inspect.signature(f))
                except Exception as e:
                    if 'is not a callable object' in str(e) or 'no signature found for builtin type' in str(e):
                        pass # For these it's fine to keep signature as None.
                    else:
                        raise Exception(f'Strange signature error on {modulename}.{varname}: {e}')
            if sig:
                self.arglist = [a.strip().replace('"',"'") for a in sig.replace('(','').replace(')','').strip()]
        if not self.arglist: # Fallback or if only_use_python_parse.
            self.arglist = python_parse.list_args(self.src_txt)
            #print('ARGLIST:', self.arglist)

    def __str__(self):
        #log_score = int(self.is_ppatched)*8+len(self.logs) # Not used.
        log_txt = ''
        if self.is_ppatched:
            log_txt = ' 👁'
        if len(self.logs)>0:
            log_txt = log_txt+' '+str(len(self.logs))
        return 'Ͼ'+self.varname_full+log_txt+'Ͽ'

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
    return bash_helpers.flex_match(query, sourcevar.varname_full)

def fn_arity_metric(sourcevar, query):
    # Includes optional args.
    arity = len(selg.arglist) if self.arglist else 0
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
        print('Usecount metric precomputing...')
        sourcevars_precompute, _ = get_all_sourcevars()
    leaf = sourcevar.varname_full.split('.')[-1] # TODO: Not just use leafs.
    n = 0
    for sv in sourcevars_precompute:
        if leaf in sv.src_txt:
            n = n+1

    return _peak(int(query), n)

########################Putting it all together#################################

def get_all_sourcevars():
    # List of sourcevars and tokens in the source.
    t0 = time.time()
    out = []
    use_modules = False
    if use_modules:
        fnames = modules.module_fnames(user_only=True)
    else:
        fnames = py_updater.walk_all_user_paths(relative_paths=False)
    src_token_counts = {}

    mod2fl = modules.module_fnames(user_only=False)
    file2mod = {}
    for m in mod2fl.keys():
        file2mod[mod2fl[m]] = m

    for fname in fnames:
        contents = file_io.fload(fname); date_mod = file_io.date_mod(fname)
        contents0 = file_io.contents_on_first_call(fname)
        src_pieces = python_parse.simple_tokens(contents)
        for p in src_pieces:
            src_token_counts[p] = src_token_counts.get(p,0)+1
        defs = python_parse.sourcecode_defs(contents, nest=True)
        defs0 = defs if contents==contents0 else python_parse.sourcecode_defs(contents0, nest=True)
        mname = file2mod.get(fname, None) # Source files that have noy yet been imported do not have a modulename.
        for dk in defs.keys():
            prepend = mname if mname else 'FILE:'+fname.replace('\\','/').replace('/','.')
            out.append(Sourcevar(filename=fname, varname_full=prepend+'.'+dk, src_txt0=defs0.get(dk,''), src_txt1=defs[dk], src_datemod=date_mod))
    t1 = time.time()
    print_elapsed_time = False
    if print_elapsed_time: # Is this function slow?
        print('get_all_sourcevars elapsed time:', t1-t0)
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
        ky = str(bashy_args[i]).lower(); val = bashy_args[i+1]
        wt = re.sub(r"\D", '', ky)
        wt = 1 if wt=='' else int(wt)
        if ky.startswith('--'):
            wt = -wt
        ky = re.sub(r"\d", '', ky.replace('--','-'))
        if ky==shall:
            verbose = int(val)
        elif ky==k_return_sv:
            return_sv = bool(val)
        elif ky=='-f':
            for sv in all_src_vars:
                sv.score = sv.score+val(sv)
        elif ky not in fns and ky not in opts:
            raise Exception('Unrecognized option:'+ky)
        elif ky in fns:
            f = fns[ky][1]
            for sv in all_src_vars:
                add_score = f(sv, val)*wt
                sv.score = sv.score+add_score
        i = i+2

    src_vars_hi2low = dquery.sort_by(all_src_vars, [-sv.score for sv in all_src_vars])
    n_return = min(len(src_vars_hi2low), verbose) # How many results to show.
    for i in range(n_return):
        if src_vars_hi2low[i].score<0.001:
            n_return = i; break
    if return_sv:
        return src_vars_hi2low[0:n_return]
    return [x.varname_full for x in src_vars_hi2low[0:n_return]]

def pythonverse_find(*bashy_args):
    # Similar to source find, but over the Pythonverse.
    TODO
