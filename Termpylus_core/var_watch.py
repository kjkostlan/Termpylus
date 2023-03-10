# Watch vars for certain effects.
import sys, time
from . import gl_data, file_io
from Termpylus_lang import pyparse, ppatch

if 'uwglobals' not in gl_data.dataset:
    # Name-qual => function; name-qual => inputs-as-dict.
    gl_data.dataset['uwglobals'] = {'logss':{}, 'txt_edits':[], 'module_watcher_codes':{}}
vglobals = gl_data.dataset['uwglobals']

############################ Var mutation watching #############################

def add_mutation_watch():
    # Vars logged on mutation (how to do this???)
    # (well-written code shouldn't have to hunt down mutations, but should != reality).
    TODO

################################ Fn watching core engine ###################################

def disk_log(*x):
    # Code freezing up? Use this function to pinpoint where.
    file_io.fappend('./softwaredump_/disklog.txt', ' '.join([str(xi) for xi in x])+'\n')

def logged_fn(modulename, var_name, f_obj):
    # Makes a logged version of the function, which behaves the same but adds to logs.
    name = modulename+'.'+var_name
    def f(*args, _SYM_name=name, **kwargs):
        #print('Logged fn call:', _SYM_name, len(args))
        kwargs1 = kwargs.copy()
        for i in range(len(args)):
            kwargs1[i] = args[i] # Number args turn into dict keys with numerical values.
        time0 = time.time()
        out = f_obj(*args, **kwargs)
        kwargs1['_time'] = [time0, time.time()]
        kwargs1['return'] = out # return is a reserved keyword.
        if _SYM_name not in vglobals['logss']:
            vglobals['logss'][_SYM_name] = []
        vglobals['logss'][_SYM_name].append(kwargs1)
        return out
    return f

def add_fn_watcher(modulename, var_name, f_code=None):
    # Changes the function in var_name to record it's inputs and outputs.
    # Replaces any old watchers.
    m = sys.modules[modulename]
    k = modulename+'.'+var_name
    ppatch.reset_var(modulename, var_name)
    f_obj = ppatch.get_var(modulename, var_name)
    if f_code is None:
        f_obj = ppatch.get_var(modulename, var_name)
    else:
        f_obj = eval(f_code) #TODO: eval in right environment.
    f = logged_fn(modulename, var_name, f_obj)

    ppatch.set_var(modulename, var_name, f)
    vglobals['module_watcher_codes'][modulename+'.'+var_name] = f_code
    return f

def rm_fn_watcher(modulename, var_name):
    ppatch.remove_patch(modulename, var_name)

def remove_module_watchers(modulename):
    var_dict = ppatch.get_vars(modulename, nest_inside_classes=True)
    for vn in var_dict.keys():
        ppatch.reset_var(modulename, vn)

def add_module_watchers(modulename):
    #Watches all functions in a module, including class methods (although class nstances may need to be re-instanced).
    remove_module_watchers(modulename) # Reset the module.
    var_dict = ppatch.get_vars(modulename, nest_inside_classes=True)
    for vn in var_dict.keys():
        if callable(var_dict[vn]):
            add_fn_watcher(modulename, vn)

def add_all_watchers_global():
    # Adds all watchers to every module (except this one!)
    # Warning: dangerous function alert may crash if not careful.
    for k in sys.modules.keys():
        if k != __name__:
            add_module_watchers(k)

def with_watcher(modulename, var_name, args, return_log=False):
    # Add watcher, run code, remove watcher.
    # Option to return_log.
    # TODO: will get more useful if we.
    logs0 = vglobals['logss'].get(modulename+'.'+varname,[])
    add_fn_watcher(modulename, var_name)
    f_obj = ppatch.get_var(modulename, var_name)
    out = f_obj(*args)
    remove_fn_watcher(modulename, var_name)
    logs1 = vglobals['logss'][modulename+'.'+varname]
    return logs1[len(logs0):] if return_log else out

def remove_all_watchers():
    for k in sys.modules.keys():
        if k != __name__:
            remove_module_watchers(k)

def bashy_set_watchers(*bashy_args):
    # Bashy commands favor brevity.
    TODO

def on_module_update(modulename):
    # Need to re-add them:
    watchers = vglobals['module_watcher_codes']
    for varq_name in watchers.keys():
        if varq_name.startswith(modulename+'.'):
            var_name = varq_name[len(modulename)+1:]
            add_fn_watcher(modulename, var_name, watchers[varq_name])

def get_logs():
    return vglobals['logss'].copy()

def remove_all_logs():
    vglobals['logss'] = {}

################################################################################

def record_txt_updates(mname, fname, old_txt, new_txt):
    # Standard record updates.
    # TODO: make it more real time, not just triggered.
    if old_txt is None:
        raise Exception('None old_text; files should be preloaded.')
    ed = pyparse.txt_edit(old_txt, new_txt)
    if str(ed)==str([0,0,'']):
        return # No edit made.
    t_now = time.time()
    ed1 = [mname, fname]+ed+[t_now]
    vglobals['txt_edits'].append(ed1)

def get_txt_edits():
    return list(vglobals['txt_edits'])

def bashy_get_txt_edits(*bashy_args):
    # Various options like a bash command.
    TODO
