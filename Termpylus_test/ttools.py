import sys

def alltrue(x):
    for xi in x:
        if not xi:
            return False
    return True

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
            x = v_obj()
            if not x:
                failed_tests.append(v)
    if len(failed_tests)>0:
        print('Tests failed: '+str(failed_tests)+' for module '+module_name)
    return len(failed_tests)==0
