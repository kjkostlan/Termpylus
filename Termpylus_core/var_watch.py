# Watch vars for certain effects.
import sys, time
from . import gl_data, strparse, ppatch

if 'uwglobals' not in gl_data.dataset:
    # Name-qual => function; name-qual => inputs-as-dict.
    gl_data.dataset['uwglobals'] = {'logs':{}, 'txt_edits':[], 'module_watcherss':{}}
vglobals = gl_data.dataset['uwglobals']

############################ Var mutation watching #############################

def add_logged_var():
    # Vars logged on mutation (how to do this???)
    # (well-written code shouldn't have to hunt down mutations, but should != reality).
    TODO

################################ Fn watching core engine ###################################

def logged_fn(modulename, var_name):
    # Makes a logged version of the function, which behaves the same but adds to logs.
    f_obj = ppatch.get_var(modulename, var_name)
    def f(_SYM_name=name, *args, **kwargs):
        kwargs1 = kwargs.copy()
        for i in range(len(args)):
            kwargs1[i] = args[i] # Number args turn into dict keys with numerical values.
        if _SYM_name not in vglobals:
            vglobals['logs'][_SYM_name] = []
        time0 = time.time()
        out = f_obj(*args, **kwargs)
        kwargs1['_time'] = [time0, time.time()]
        kwargs1['return'] = out # return is a reserved keyword.
        vglobals[_SYM_name].append(kwargs1)
        return out
    return f

def add_fn_watcher(modulename, var_name, f_code=None):
    # Changes the function in var_name to record it's inputs and outputs.
    # Replaces any old watchers.
    # f_code can change the code passed into f.
    m = sys.modules[modulename]
    k = modulename+'.'+var_name
    f_obj = ppatch.get_var(modulename, var_name)
    if modified_code is None:
        f_obj1 = vglobals.get('original_fns', f_obj)
    else:
        f_obj1 = eval(f_code) #TODO: eval in right environment.
    f = logged_fn(modulename, var_name, f_obj)

    ppatch.set_var(modulename, var_name, f)
    vglobals['module_watcherss'][modulename][var_name] = f_code
    return f

def rm_fn_watcher(modulename, var_name):
    ppatch.remove_patch(modulename, var_name)

def add_module_watchers(modulename):
    TODO

def add_all_watchers_global():
    blockset = {add_logged_var, logged_fn, add_fn_watcher, rm_fn_watcher} # Do not add watchers here, even when we add "all" watchers.
    # Is this too many?
    #sys.modules[]
    TODO

def with_watcher(modulename, var_name, args):
    # Add watcher, run code, remove watcher.
    TODO

def remove_module_watchers(modulename):
    #sys.modules[]
    TODO

def remove_all_watchers():
    TODO

def on_module_update(modulename):
    # Need to re-add them:
    watchers = vglobals['module_watcherss'].get(modulename, {})
    for var_name in watchers.keys():
        add_fn_watcher(modulename, var_name, watchers[var_name])

def get_logs(fn_name_qual):
    return vglobals['logs'].copy()

def remove_all_logs():
    vglobals['logs'] = {}

def set_watchers(bashy_args):
    TODO

def record_txt_updates(mname, fname, old_txt, new_txt):
    # Standard record updates.
    # TODO: make it more real time, not just triggered.
    if old_txt is None:
        raise Exception('None old_text; files should be preloaded.')
    ed = strparse.txt_edit(old_txt, new_txt)
    if str(ed)==str([0,0,'']):
        return # No edit made.
    t_now = time.time()
    ed1 = [mname, fname]+ed+[t_now]
    vglobals['txt_edits'].append(ed1)

def get_txt_edits(*args):
    return list(vglobals['txt_edits'])


