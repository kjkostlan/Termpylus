# Module loading and updating.
import sys, os, importlib, io, time
from Termpylus_py import usetrack

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

# Singleton globals only set up once.
try:
    _ = mglobals
except NameError:
    mglobals = dict()
    mglobals['filecontents'] = {}
    mglobals['filemodified'] = {} # Alternative to checking contents.
    mglobals['pathprepends'] = set() # keep track of what is added to the import path.

def is_user(modulename, filename):
    # user files.
    filename = filename.replace('\\','/')
    if 'syspyfolderlist' not in mglobals: # what modules
        test_modules = ['os', 'importlib', 'io']
        folders = set()
        for t in test_modules:
            folders.add(sys.modules[t].__file__.replace('\\','/').replace(t+'.py','').replace('__init__.py',''))
        mglobals['syspyfolderlist'] = folders
    no_list = mglobals['syspyfolderlist']
    if filename.endswith('.pyd'):
        return False # User files don't use .pyd
    for n in no_list:
        if n in filename:
            return False
    return True

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

def module_dict():
    return sys.modules

def module_file(m):
    if type(m) is str:
        m = sys.modules[m]
    if '__file__' not in m.__dict__:
        return None
    return os.path.abspath(m.__file__).replace('\\','/')

def module_fnames(user_only=False):
    # Only modules that have files, and dict values are module names.
    # Also can restrict to user-only files.
    d = module_dict()
    out = {}
    for k in d.keys():
        if '__file__' in d[k].__dict__:
            fname = d[k].__file__
            if fname is not None:
                if not user_only or is_user(k, fname):
                    out[k] = fname.replace('\\','/')
    return out

def add_to_path(folder_name):
    # https://docs.python.org/3/library/sys.html#sys.path
    sys.path = [os.path.realpath(folder_name)]+sys.path
    mglobals['pathprepends'].add(folder_name)

def pop_from_path():
    mglobals['pathprepends'].remove(sys.path[0])
    sys.path = sys.path[1:]

def _fupdate(fname, modulename):
    if modulename is not None:
        clear_pycache(fname)
        importlib.reload(sys.modules[modulename])
    txt = contents(fname)
    if fname in mglobals['filecontents']:
        old_txt = mglobals['filecontents'][fname]
        if old_txt != txt and modulename is not None:
            usetrack.record_updates(modulename, fname, old_txt, txt)
    else:
        old_txt = None
    mglobals['filecontents'][fname] = txt
    mglobals['filemodified'][fname] = time.time() # Does date modified use the same as our own time?
    return old_txt, txt

def update_one_module(modulename, use_date=False, update_on_first_see=False):
    # The module must already be in the file.
    fname = os.path.realpath(sys.modules[modulename].__file__).replace('\\','/')
    if fname not in mglobals['filecontents']: # first time seen.
        txt = None; tmod = None
        pass
    elif use_date:
        tmod = date_mod(fname); txt = None
        if tmod == mglobals['filemodified'][fname]:
            return False, None
    else:
        txt = contents(fname); tmod = None
        if txt == mglobals['filecontents'][fname]:
            return False, None

    if txt is None:
        txt = contents(fname)
    if tmod is None:
        tmod = date_mod(fname)

    mupdate=None
    if update_on_first_see or fname in mglobals['filecontents']:
        if (not use_date and mglobals['filecontents'][fname]!=txt) or (use_date and mglobals['filemodified'][fname]!=tmod):
            if modulename == '__main__' and (not update_on_first_see): # odd case, generates spec not found error.
                raise Exception('Cannot update the main module for some reason. Need to restart when the Termpylus_main .py file changes.')
            elif modulename != '__main__':
                if printouts:
                    print('Reloading:', modulename)
                mupdate = modulename

    [old_contents, txt] = _fupdate(fname, mupdate)
    return True, [old_contents, txt]

def update_all_modules(use_date=False, update_on_first_see=False):
    # use_date True should be faster but maybe less accurate.
    # Returns {mname: [fname, old, new]}
    fnames = module_fnames(True)
    out = {}
    for k in fnames.keys():
        changed, old_new = update_one_module(k, use_date, update_on_first_see)
        if changed:
            out[k] = [fnames[k]]+old_new
    return out

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
                _fupdate(fname, k)
                return k
        raise Exception('Filename not in listed modules:' + fname)
