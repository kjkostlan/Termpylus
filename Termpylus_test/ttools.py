import sys
import numpy as np
from Termpylus_core import var_watch

def alltrue(x):
    if type(x) is dict:
        x = list(x.values())
    for xi in x:
        if not xi:
            return False
    return True

def ints_eq(a,b):
    # Equality of all integer elements, handles lists and/or np arrays.
    if len(a) != len(b):
        return False
    return np.sum(np.abs(np.asarray(a)-b))==0

def run_tests(module_name):
    # call as: "ttools.run_tests(__name__)"
    d = sys.modules[module_name].__dict__
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
            var_watch.disk_log('Starting unit test of:', v)
            x = v_obj()
            if not x:
                failed_tests.append(v)
            var_watch.disk_log('Finished unit test of:', v, 'pass?', x)

    if len(failed_tests)>0:
        print('Tests failed: '+str(failed_tests)+' for module '+module_name)
    return len(failed_tests)==0
