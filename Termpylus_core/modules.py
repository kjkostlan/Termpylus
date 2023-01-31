# Loading new modules and updating modules (but not file io)
# Also: functions that get variables from modules.
import sys, os, importlib, io
from . import gl_data

if 'modules_globals' not in gl_data.dataset:
    mglobals = dict()
    mglobals['pathprepends'] = set() # keep track of what is added to the import path.
    mglobals['varflush_queue'] = [] # Updating these can be a heavy task.

    gl_data.dataset['modules_globals'] = mglobals
mglobals = gl_data.dataset['modules_globals']

def add_to_path(folder_name):
    # https://docs.python.org/3/library/sys.html#sys.path
    sys.path = [os.path.realpath(folder_name)]+sys.path
    mglobals['pathprepends'].add(folder_name)

def pop_from_path():
    mglobals['pathprepends'].remove(sys.path[0])
    sys.path = sys.path[1:]

def is_user(modulename, filename):
    # Only change user files. TODO: maybe there is a better way to handle this?
    filename = filename.replace('\\','/')
    if 'syspyfolderlist' not in mglobals: # what modules
        test_modules = ['os', 'importlib', 'io']
        folders = set()
        for t in test_modules:
            folders.add(sys.modules[t].__file__.replace('\\','/').replace(t+'.py','').replace('__init__.py',''))
        mglobals['syspyfolderlist'] = folders
    no_list = mglobals['syspyfolderlist']
    if 'PythonSoftwareFoundation.Python' in filename: # Heuristic that worked with numpy:
        return False
    if filename.endswith('.pyd'):
        return False # User files don't use .pyd
    for n in no_list:
        if n in filename:
            return False
    return True

def module_file(m):
    if type(m) is str:
        m = sys.modules[m]
    if '__file__' not in m.__dict__ or m.__file__ is None:
        return None
    return os.path.abspath(m.__file__).replace('\\','/')

def module_fnames(user_only=False):
    # Only modules that have files, and dict values are module names.
    # Also can restrict to user-only files.
    out = {}
    for k in sys.modules.keys():
        fname = module_file(sys.modules[k])
        if fname is not None and (not user_only or is_user(k, fname)):
            out[k] = fname.replace('\\','/')
    return out

def get_var(modulename, var_name):
    # Gets the f_object.
    pieces = var_name.split('.')
    TODO

def set_var(modulename, var_name, x):
    # m.__dict__[var_name] = x but more complex for classes.
    TODO

def _get_vars_core(out, x, subpath, nest, usedids):
    d = x.__dict__ # Found in both modules and classes.
    for k in d.keys():
        if id(d[k]) in usedids:
            continue # Avoids infinite loops with circular class references.
        if k.startswith('__') and k.endswith('__'): # Oddball python stuff we do not need.
            continue
        out[subpath+k] = d[k]
        usedids.add(id(d[k]))
        if nest and type(d[k]) is type: # Classes.
            _get_vars_core(out, d[k], subpath+k+'.', nest, usedids)

def get_vars(modulename, nest_inside_classes=True):
    # Map from symbol to name.
    out = {}
    usedids = set()
    x = sys.modules[modulename]
    _get_vars_core(out, x, '', nest_inside_classes, usedids)
    return out

def get_all_vars(nest_inside_classes=True):
    TODO

def module_from_file(modulename, pyfname, exec_module=True):
    # Creates a module from a file.
    if modulename in sys.modules: # already exists, just update it.
        pyfname0 = module_file(modulename)
        if pyfname0 == pyfname:
            update_one_module(modulename, False)
            return sys.modules[modulename]
        elif pyfname0 is not None:
            pyfname = os.path.realpath(pyfname).replace('\\','/')
            if pyfname != pyfname0:
                raise Exception('Shadowing modulename: '+modulename+' Old py.file: '+pyfname0+ 'New py.file '+pyfname)
    mglobals['filecontents'][pyfname] = contents(pyfname)
    mglobals['filemodified'][pyfname] = date_mod(pyfname)

    #https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
    spec = importlib.util.spec_from_file_location(modulename, pyfname)
    if spec is None:
        raise Exception('None spec')
    foo = importlib.util.module_from_spec(spec)
    sys.modules[modulename] = foo
    if exec_module:
        spec.loader.exec_module(foo)
    return foo