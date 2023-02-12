# More hot commands.
# Functions go here for ease of acess and are avaialbe w/o import.
import sys
from Termpylus_core import var_watch, dquery, var_watch

def utest_this(args):
    # Unitests.
    print('**************Running unit tests**************')
    from Termpylus_test import test_pyrun, test_shell, test_walk, test_varmodtrack, test_pythonverse
    n_fail = 0
    for t_module in [test_pyrun, test_shell, test_walk, test_varmodtrack, test_pythonverse]:
        if not t_module.run_tests():
            print('>>testing failed for:', t_module)
            n_fail = n_fail+1
    print('!!>>!!>>Number fail:', n_fail)
    return n_fail==0

def splat_here(modulename):
    kvs = cmds1()
    module = sys.modules[modulename]
    for k in kvs.keys():
        module.__dict__[k] = kvs[k]

def cmds1():
    #These extra cmds are for python editing.
    # Will add many more...
    def t1(args):
        from Termpylus_test import scratchpad # Delay import b/c it is importing many modules.
        return scratchpad.some_test(args)
    def _unwrap(d):
        if type(d) is list:
            d = d[0]
        from Termpylus_py import walk
        return walk.unwrap(d)
    def _pflush(args):
        from Termpylus_py import mload
        return mload.function_flush()
    out = {}
    def _help(args):
        return 'Available non-bash cmds: '+str(list(out.keys()))
    def _pfind(bashy_args):
        super_var_storage = modules.get_all_vars()
        dquery.generic_find(bashy_args, super_var_storage)
    def _python_cmd(bashy_args):
        TODO
    out['utest'] = utest_this
    out['test1'] = t1
    out['pwatch'] = var_watch.bashy_set_watchers
    out['pfind'] = _pfind
    out['pflush'] = _pflush
    out['changes'] = var_watch.bashy_get_txt_edits
    out['dunwrap'] = _unwrap # Useful to see the total size of data structure.
    out['help'] = _help
    out['python'] = _python_cmd
    return out
