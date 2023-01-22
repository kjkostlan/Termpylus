# Module loading and updating.
import sys, os, importlib, io, time
from Termpylus_py import usetrack, fnwatch

printouts=False

#list(pkgutil.iter_modules()) # even more full.
'''
The name shadowing trap
Another common trap, especially for beginners, is using a local module name that
shadows the name of a standard library or third party package or module that the
application relies on. One particularly surprising way to run afoul of this trap
is by using such a name for a script, as this then combines with the previous
“executing the main module twice” trap to cause trouble. For example, if
experimenting to learn more about Python’s socket module, you may be inclined to
call your experimental script socket.py. It turns out this is a really bad idea,
as using such a name means the Python interpreter can no longer find the real
socket module in the standard library, as the apparent socket module in the
current directory gets in the way.

Many users will have experienced the issue of trying to use a submodule when only
importing the package that it is in:

$ python3
>>> import logging
>>> logging.config
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'module' object has no attribute 'config'

But it is less common knowledge that when a submodule is loaded anywhere it is
automatically added to the global namespace of the package:

$ echo "import logging.config" > weirdimport.py
$ python3
>>> import weirdimport
>>> import logging
>>> logging.config
<module 'logging.config' from '.../Python.framework/Versions/3.4/lib/python3.4/logging/config.py'>

'''

class ModuleUpdate:
    # How to look up var from id:
    # https://stackoverflow.com/questions/15011674/is-it-possible-to-dereference-variable-ids
    '''
    import _ctypes

    def di(obj_id):
        """ Inverse of id() function. """
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

# Singleton globals only set up once.
try:
    _ = mglobals
except NameError:
    mglobals = dict()
    mglobals['filecontents'] = {}
    mglobals['filemodified'] = {} # Alternative to checking contents.
    mglobals['pathprepends'] = set() # keep track of what is added to the import path.
    mglobals['varflush_queue'] = [] # Updating these can be a heavy task.

def _fupdate(fname, modulename):
    old_vars = fnwatch.get_vars(modulename)

    clear_pycache(fname)
    importlib.reload(sys.modules[modulename])
    new_txt = contents(fname)
    if fname in mglobals['filecontents']:
        old_txt = mglobals['filecontents'][fname]
        if old_txt != new_txt:
            usetrack.record_updates(modulename, fname, old_txt, new_txt)
    else:
        old_txt = None
    mglobals['filecontents'][fname] = new_txt
    mglobals['filemodified'][fname] = time.time() # Does date modified use the same as our own time?

    new_vars = fnwatch.get_vars(modulename)

    out = ModuleUpdate(modulename, old_txt, new_txt, old_vars, new_vars)
    mglobals['varflush_queue'].append(out)
    return out

################################Paths###########################################

def add_to_path(folder_name):
    # https://docs.python.org/3/library/sys.html#sys.path
    sys.path = [os.path.realpath(folder_name)]+sys.path
    mglobals['pathprepends'].add(folder_name)

def pop_from_path():
    mglobals['pathprepends'].remove(sys.path[0])
    sys.path = sys.path[1:]

def is_user(modulename, filename):
    # user files. TODO: maybe there is a better way to handle this?
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

############################# Files and folders #######################

def contents(fname):
    if not os.path.isfile(fname):
        return None
    with io.open(fname, mode="r", encoding="utf-8") as file_obj:
        try:
            x = file_obj.read()
        except UnicodeDecodeError:
            raise Exception('No UTF-8 for:', fname)
        return x.replace('\r\n','\n')

def date_mod(fname):
    return os.path.getmtime(fname)

def fsave(fname, txt, update_module=True):
    # Updates modules and records changes if fname corresponds to a module.
    fname = os.path.abspath(fname).replace('\\','/')
    old_txt = contents(fname)
    with io.open(fname, mode="w", encoding="utf-8") as file_obj:
        file_obj.write(txt)
    if update_module:
        f = module_fnames(True)
        for k in f: # a little inefficient to loop through each modulename.
            if f[k] == fname and old_txt != txt:
                if printouts:
                    print('Saving to module:', k)
                return _fupdate(fname, k)
        raise Exception('Filename not in listed modules:' + fname)

def clear_pycache(filename):
    # This can intefere with updating.
    cachefolder = os.path.dirname(filename)+'/__pycache__'
    leaf = os.path.basename(filename).replace('.py','')
    if os.path.isdir(cachefolder):
        leaves = os.listdir(cachefolder)
        for l in leaves:
            if leaf in l:
                if printouts:
                    print('Deleting cached file:', cachefolder+'/'+l)
                os.remove(cachefolder+'/'+l)

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

def startup_cache_sources():
    # Stores the file contents and date-mod to compare against for updating.
    for fname in module_fnames(True).values():
        mglobals['filecontents'][fname] = contents(fname)
        mglobals['filemodified'][fname] = date_mod(fname)

#############################Module updating####################################

def needs_update(modulename, update_on_first_see=True, use_date=False):
    fname = module_file(modulename)
    if fname not in mglobals['filecontents']: # first time seen.
        return update_on_first_see
    elif use_date:
        return mglobals['filemodified'][fname] < date_mod(fname)
    else:
        return mglobals['filecontents'][fname] != contents(fname)

def update_one_module(modulename, fname=None):
    # The module must already be in the file.
    print('Updating MODULE:', modulename)
    if modulename == '__main__' and (not update_on_first_see): # odd case, generates spec not found error.
        raise Exception('Cannot update the main module for some reason. Need to restart when the Termpylus_main.py file changes.')
    if fname is None:
        fname = module_file(modulename)
    if fname is None:
        raise Exception('No fname supplied and cannot find the file.')

    return _fupdate(fname, modulename)

def update_user_changed_modules(update_on_first_see=True, use_date=False):
    # Updates modules that aren't pip packages or builtin.
    # use_date True should be faster but maybe less accurate.
    # Returns {mname: ModuleUpdate object}
    fnames = module_fnames(True)
    #print('Updating USER MODULES, '+str(len(mglobals['filecontents']))+' files currently cached,', str(len(fnames)), 'user modules recognized.')

    out = {}
    for m in fnames.keys():
        if needs_update(m, update_on_first_see, use_date):
            out[m] = update_one_module(m, fnames[m])
    return out

def function_flush():
    # Looks high and low to the far corners of the Pythonverse for references to out-of-date module functions.
    # Replaces them with the newest version when necessary.
    # Can be an expensive and slow function, run when things seem to not be updated.
    #mglobals['varflush_queue']
    TODO