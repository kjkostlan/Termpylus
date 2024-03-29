# Call this to update several functions.
import sys, os, importlib, time
from . import gl_data, var_watch, file_io, todict
from Termpylus_lang import modules, ppatch

if 'updater_globals' not in gl_data.dataset:
    uglobals = dict()
    uglobals['filecontents'] = {}
    uglobals['filemodified'] = {} # Alternative to checking contents.
    uglobals['varflush_queue'] = []
    gl_data.dataset['updater_globals'] = uglobals
uglobals = gl_data.dataset['updater_globals']

printouts = True

class ModuleUpdate:
    # How to look up var from id:
    # https://stackoverflow.com/questions/15011674/is-it-possible-to-dereference-variable-ids
    '''
    import _ctypes

    def di(obj_id):
        return _ctypes.PyObj_FromPtr(obj_id)

    # OR this:
    import ctypes
    a = "hello world"
    print ctypes.cast(id(a), ctypes.py_object).value
    '''
    # (But this is dangerous, so lets not rely on it unless we really need to).
    # Stores the module updating.
    def __init__(self, modulename, old_txt, new_txt, old_vars, new_vars):
        self.modulename = modulename
        self.old_txt = old_txt
        self.new_txt = new_txt

        self.old_new_pairs = {}
        for k in new_vars.keys():
            if k in old_vars and old_vars[k] is not new_vars[k]:
                self.old_new_pairs[k] = [old_vars[k], new_vars[k]]

def _fupdate(fname, modulename):
    old_vars = ppatch.get_vars(modulename)
    fname = os.path.abspath(fname).replace('\\','/')

    file_io.clear_pycache(fname)
    importlib.reload(sys.modules[modulename])
    new_txt = file_io.contents(fname)
    if fname in uglobals['filecontents']:
        old_txt = uglobals['filecontents'][fname]
        if old_txt != new_txt:
            var_watch.record_txt_updates(modulename, fname, old_txt, new_txt)
    else:
        old_txt = None
    uglobals['filecontents'][fname] = new_txt
    uglobals['filemodified'][fname] = time.time() # Does date modified use the same as our own time?

    new_vars = ppatch.get_vars(modulename)

    out = ModuleUpdate(modulename, old_txt, new_txt, old_vars, new_vars)
    uglobals['varflush_queue'].append(out)
    return out

def save_py_file(py_file, contents, assert_py_module=False):
    # Saves a python file and makes all the needed updates to the modules.
    py_file = os.path.abspath(py_file).replace('\\','/')

    old_txt = file_io.contents(py_file)
    file_io.fsave(py_file, contents)

    f = modules.module_fnames(True)
    for k in f: # a little inefficient to loop through each modulename.
        if f[k] == py_file and old_txt != contents:
            if printouts:
                print('Saving to module:', k)
            return _fupdate(py_file, k)
    if assert_py_module:
        raise Exception('Filename not in listed modules:' + py_file)

def needs_update(modulename, update_on_first_see=True, use_date=False):
    fname = modules.module_file(modulename)
    if fname not in uglobals['filecontents']: # first time seen.
        return update_on_first_see
    elif use_date:
        return uglobals['filemodified'][fname] < file_io.date_mod(fname)
    else:
        return uglobals['filecontents'][fname] != file_io.contents(fname)

def update_one_module(modulename, fname=None, assert_main=True):
    # The module must already be in the file.
    if modulename == '__main__' and assert_main: # odd case, generates spec not found error.
        raise Exception('Cannot update the main module for some reason. Need to restart when the Termpylus_main.py file changes.')
    elif modulename == '__main__':
        return
    print('Updating MODULE:', modulename)
    if fname is None:
        fname = modules.module_file(modulename)
    if fname is None:
        raise Exception('No fname supplied and cannot find the file.')
    var_watch.on_module_update(modulename)

    return _fupdate(fname, modulename)

def update_user_changed_modules(update_on_first_see=True, use_date=False):
    # Updates modules that aren't pip packages or builtin.
    # use_date True should be faster but maybe miss some files?
    # Returns {mname: ModuleUpdate object}
    fnames = modules.module_fnames(True)
    #print('Updating USER MODULES, '+str(len(uglobals['filecontents']))+' files currently cached,', str(len(fnames)), 'user modules recognized.')

    out = {}
    for m in fnames.keys():
        if needs_update(m, update_on_first_see, use_date):
            out[m] = update_one_module(m, fnames[m], not update_on_first_see)
    return out

def startup_cache_sources(modulenames=None):
    # Stores the file contents and date-mod to compare against for updating.
    if modulenames is None:
        filenames = modules.module_fnames(True).values()
    else:
        filenames = [modules.module_file(m) for m in modulenames]
    for fname in filenames:
        if fname is not None and fname.endswith('.py'):
            uglobals['filecontents'][fname] = file_io.contents(fname) # no need to call full _fuptate.
            uglobals['filemodified'][fname] = file_io.date_mod(fname)

def startup_python(modulename, pyfname, exec_module=True):
    out = modules.module_from_file(modulename, pyfname, exec_module)
    uglobals['filecontents'][pyfname] = file_io.contents(pyfname) # no need to call full _fuptate.
    uglobals['filemodified'][pyfname] = file_io.date_mod(pyfname)
    return out

####################### Updating the python objects directly ###################

def default_update_object(x, kvs):
    # Updates x by setting all keys in kvs to thier values.
    TODO

def same_inst_method(x,y):
    # Are x and y the same methods of the same object instance? (False unless both are methods).
    # Python generates methods dynamically on an attribute look-up so "is" won't work.
    if str(type(x)) == "<class 'method'>" and str(type(y)) == "<class 'method'>":
        return x.__self__ is y.__self__
    return False

def default_eq_for_update(x,y):
    # True here means we need to update the values.
    return x is y or same_inst_method(x,y)

def recursive_obj_update(todict_result, replace_pair, update_fn=default_update_object, eq_fn=default_eq_for_update):
    # Recursivly applies replace_pair to todict_result, changing objects held in
    # todict_result[<some path>][todict.ob_key].
    TODO

def function_flush():
    # Looks high and low to the far corners of the Pythonverse for references to out-of-date module functions.
    # Replaces them with the newest version when necessary.
    # Can be an expensive and slow function, run when things seem to not be updated.
    # Will NOT work on class methods passed as a fn param, since these attributes are generated dynamicalls.
    uglobals['varflush_queue']
    TODO
