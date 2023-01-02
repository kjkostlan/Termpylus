import sys, os, imp
from Termpylus_shell import shellpython

def _alltrue(x):
    for xi in x:
        if not xi:
            return False
    return True

def test_py_import0():
    # Requires a syster folder so it can't really run as a standalone test.

    kys0 = list(sys.modules.keys())
    folder = os.path.dirname(os.path.realpath(__file__)).replace('\\','/')
    folder = folder.replace('Termpylus','')+'/../simplypyimport/'
    if not os.path.exists(folder):
        print('WARNING: cant run test_py_import due to lack of folder outside our folder. Will return True without testing.')
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

    print('Py import test',mdle.go1())
    print('test_py_import All moudles:', list(sys.modules.keys()))
    print('test_py_import NEW moudles:', set(sys.modules.keys())-set(kys0))

    return True

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
        raise Exception('Tests failed: '+str(failed_tests))
    return True
