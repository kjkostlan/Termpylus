# Do we need the builting unittest lib?
import sys, traceback
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

def run_tests(module_name, disk_write_report=True):
    # Runs all fns that have 'test' in them, with a few exceptions.
    # Retuns a map of what failed. The modulename must be imported.
    if type(module_name) is type(sys):
        module_name = module_name.__name__

    d = sys.modules[module_name].__dict__
    vars = list(d.keys())
    vars.sort()
    failed_tests = {}
    for v in vars:
        if v.startswith('_'):
            continue
        if 'run_tests' in v or 'prepare_tests' in v or 'postpare_tests' in v:
            continue
        if 'test' not in v:
            continue
        v_obj = d[v]
        if type(v_obj) is not type(sys):
            if disk_write_report:
                var_watch.disk_log('Starting unit test of:', v)
            try:
                x = v_obj()
                if not x:
                    failed_tests[module_name+'.'+v] = 'fail w/o err'
            except Exception as e:
                failed_tests[module_name+'.'+v] = str(traceback.format_exc())
            if disk_write_report:
                var_watch.disk_log('Finished unit test of:', v, 'pass?', x)

    return failed_tests
