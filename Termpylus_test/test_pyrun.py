import sys, os, imp
from Termpylus_py import usetrack, mload, fnwatch
from Termpylus_shell import shellpython

def _alltrue(x):
    for xi in x:
        if not xi:
            return False
    return True

def test_py_import0():
    # Optional extra test. Returns True unless there is a simplypyimport test folder
    # outside of our main directory for which it will try importing it.
    # If this test fails (with the right folder & contents) opening a project will fail.
    kys0 = list(sys.modules.keys())
    folder = os.path.dirname(os.path.realpath(__file__)).replace('\\','/')
    folder = folder.replace('Termpylus','')+'/../simplypyimport/'
    if not os.path.exists(folder):
        print('Make sure opening a Python project works.')
        return True

    # Sys.path append? https://docs.python.org/3/library/sys.html#sys.path
    #sys.path = [os.path.realpath(folder)]+sys.path
    mdle = shellpython.python([folder+"smain.py"])

    # https://docs.python.org/3/reference/import.html
    # add a new import hook to sys.meta_path.
    # (too complex, we need a spec object on return)

    #mdleoo = shellpython.python([folder+"stpkg", "-m", "stpkg"])
    # https://www.oreilly.com/library/view/python-cookbook/0596001673/ch15s03.html
    #pkh = imp.new_module('stpkg'); sys.modules['stpkg'] = pkg
    #pkg.__spec__.submodule_search_locations =
    #mdle = shellpython.python([folder+"soutside.py", "-m", "soutside"])
    #mdle = shellpython.python([folder+"smain.py", "-m", "smain"])

    #https://peps.python.org/pep-0302/
    #mdleoo = shellpython.python([folder+"stpkg/unicode.py", "-m", "stpkg.unicode"])
    #mdleoo = shellpython.python([folder+"stpkg/mathy.py", "-m", "stpkg.mathy"]) # needed.
    #mdleo = shellpython.python([folder+"soutside.py", "-m", "soutside"])
    # If out of order we get: ModuleNotFoundError: No module named 'soutside'
    #mdleo = shellpython.python([folder+"soutside.py"]) # Outer level pyhton filenames are automatically set.

    # Import ... as ... does not change the name.

    #print('Py import test',mdle.go1())
    #print('test_py_import All moudles:', list(sys.modules.keys()))
    #print('test_py_import NEW moudles:', set(sys.modules.keys())-set(kys0))

    return True

def test_py_update():
    #print('Fullpath:', os.path.realpath(fname).replace('\\','/'))

    #print('TEST edit:', usetrack.txt_edit('foo123bar', 'foo456bar'))
    #return False

    from . import test_changeme # adds to the sys.modules
    val0 = test_changeme.mathy_function(1000)
    mload.update_one_module(test_changeme.__name__)
    #print('Val00 is:', val0)
    fname = './Termpylus_test/test_changeme.py'
    #x0 = mload.update_all_modules(use_date=False, update_on_first_see=False)
    txt = mload.contents(fname)
    if '1234' not in txt:
        txt0 = txt.replace('4321','1234')
        mload.fsave(fname, txt0)
        raise Exception('Aborted test_py_update due to file save not bieng reverted. Try again.')
    eds0 = usetrack.get_edits()
    T0 = val0==1000+1234

    txt1 = txt.replace('1234','4321')
    if txt1==txt:
        raise Exception('The change failed.')
    mload.fsave(fname, txt1)
    #x1 = mload.update_all_modules(use_date=False, update_on_first_see=False)
    val1 = test_changeme.mathy_function(1000)
    eds1 = usetrack.get_edits()
    T1 = val1==1000+4321
    mload.fsave(fname, txt) # revert.

    #print('Values 01:', val0, val1)
    #print('edits len:', len(eds0), len(eds1))
    last_ed = eds1[-1]
    #print('last_ed:', last_ed)
    ed_len = (len(eds1)==len(eds0)+1)
    ed_test = last_ed[4] == '1234' and last_ed[5] == '4321'
    #print('criteria:', T0, T1, ed_len, ed_test)
    #print('Stuff test_py_update:', val0, val1)
    return T0 and T1 and ed_len and ed_test

def test_file_caches():
    mload.startup_cache_sources()
    mglob = mload.mglobals
    fnamemap = mload.module_fnames(True)
    t0 = len(mglob['filecontents'])>8
    t1 = set(mglob['filecontents'].keys())==set(mglob['filemodified'].keys())
    t2 = 'test_file_caches' in mglob['filecontents'][fnamemap['Termpylus_test.test_pyrun']]
    t3 = os.path.isfile(list(fnamemap.values())[4])
    return t0 and t1 and t2 and t3

def test_vars_from_module():
    modulename = '__main__'
    x = sys.modules[modulename]
    vmap = fnwatch.get_vars(modulename, nest_inside_classes=True)
    vmap0 = fnwatch.get_vars(modulename, nest_inside_classes=False)
    t0 = vmap['GUI'] is vmap0['GUI']
    t1 = 'GUI.resize' in vmap and 'GUI.resize' not in vmap0
    t2 = vmap['GUI'] is x.GUI
    t3 = vmap['GUI.set_shell_output'] is x.GUI.set_shell_output
    t4 = vmap['root'] is x.root
    return t0 and t1 and t2 and t3 and t4

def run_tests():
    d = sys.modules[__name__].__dict__
    vars = list(d.keys())
    vars.sort()
    failed_tests = []
    for v in vars:
        if '__' in v:
            continue
        if 'run_tests' in v:
            continue
        if 'test' not in v:
            continue
        v_obj = d[v]
        if type(v_obj) is not type(sys):
            x = v_obj()
            if not x:
                failed_tests.append(v)
    if len(failed_tests)>0:
        print('Tests failed: '+str(failed_tests))
    return len(failed_tests)==0
