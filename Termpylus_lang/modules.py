# Loading new modules and updating modules (but not file io)
import sys, os, importlib, io, re
from Termpylus_core import gl_data, file_io
from . import pyparse

if 'modules_globals' not in gl_data.dataset:
    mglobals = dict()
    mglobals['pathprepends'] = set() # keep track of what is added to the import path.
    mglobals['varflush_queue'] = [] # Updating these can be a heavy task.

    gl_data.dataset['modules_globals'] = mglobals
mglobals = gl_data.dataset['modules_globals']

def add_to_path(folder_name):
    # https://docs.python.org/3/library/sys.html#sys.path
    folder_name = file_io.termp_abs_path(folder_name)
    if folder_name not in set(sys.path):
        sys.path = [file_io.termp_abs_path(folder_name)]+sys.path
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
    return file_io.termp_abs_path(m.__file__).replace('\\','/')

def module_fnames(user_only=False):
    # Only modules that have files, and dict values are module names.
    # Also can restrict to user-only files.
    out = {}
    for k in sys.modules.keys():
        fname = module_file(sys.modules[k])
        if fname is not None and (not user_only or is_user(k, fname)):
            out[k] = fname.replace('\\','/')
    return out

def module_from_file(modulename, pyfname, exec_module=True):
    # Creates a module from a file. Generally the modulename will be foo.bar if the
    # file is path/to/external/project/foo/bar.py
    if modulename in sys.modules: # already exists, just update it.
        pyfname0 = module_file(modulename)
        if pyfname0 == pyfname:
            #update_one_module(modulename, False) # Shouldn't be necessary as long as update_user_changed_modules is bieng called.
            return sys.modules[modulename]
        elif pyfname0 is not None:
            pyfname = file_io.termp_abs_path(pyfname).replace('\\','/')
            if pyfname != pyfname0:
                raise Exception('Shadowing modulename: '+modulename+' Old py.file: '+pyfname0+ 'New py.file '+pyfname)

    folder_name = os.path.dirname(file_io.termp_abs_path(pyfname))
    add_to_path(folder_name)

    #https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
    spec = importlib.util.spec_from_file_location(modulename, pyfname)
    if spec is None:
        raise Exception('None spec')
    foo = importlib.util.module_from_spec(spec)
    sys.modules[modulename] = foo
    if exec_module:
        spec.loader.exec_module(foo)
    return foo

def get_main_blocks(modulename):
    # The module must be loaded.
    # Returns a vector.
    txt = file_io.contents(module_file(modulename))
    def _line_f(line):
        no_comment = re.sub(r'#.*', '', line)
        gold = 'if __name__ == "__main__":'
        _rep = lambda txt: txt.replace('==','is').replace(' ','').replace('"',"'").strip()
        return _rep(no_comment)==_rep(gold)
    main_contents = pyparse.statement_contents(txt, _line_f, dedent=True)
    return main_contents
