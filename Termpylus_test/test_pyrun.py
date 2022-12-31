
def _alltrue(x):
    for xi in x:
        if not xi:
            return False
    return True

def test_py_import0():
    # Requires a syster folder so it can't really run as a standalone test.
    folder = os.path.dirname(os.path.realpath(__file__)).replace('\\','/')
    folder = folder.replace('Termpylus','')+'/../simplypyimport/'
    if not os.path.exists(folder):
        print('WARNING: cant run test_py_import due to lack of folder outside our folder. Will return True without testing.')
        return True
    mdleo = shellpython.python([folder+"soutside.py", "-m", "soutside"])
    # If out of order we get: ModuleNotFoundError: No module named 'soutside'
    #mdleo = shellpython.python([folder+"soutside.py"]) # Outer level pyhton filenames are automatically set.
    mdle = shellpython.python([folder+"smain.py", "-m", "smain"])

    # Import ... as ... does not change the name.

    print('Py import test',mdle.go1())
    print('test_py_import All moudles:', list(sys.modules.keys()))

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
