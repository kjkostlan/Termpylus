# More hot commands.
# Functions go here for ease of acess and are avaialbe w/o import.
import sys
from Termpylus_py import usetrack, fsearch, fnwatch

def utest_this(args):
    # Unitests.
    print('**Running unit tests**')
    from Termpylus_test import test_pyrun # Delay b/c better to not have circular dependencies and testing may import a lot of clutter.
    ok = True
    if not test_pyrun.run_tests():
        ok = False
        print('>>test_pyrun module failed.')
    from Termpylus_test import test_shell
    if not test_shell.run_tests():
        ok = False
        print('>>test_shell module failed.')
    return ok

def cmds1():
    #These extra cmds are for python editing.
    # Will add many more...
    def t1(args):
        from Termpylus_test import test_scratchpad # Delay import b/c it is importing many modules.
        return test_scratchpad.some_test(args)
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
    out['utest'] = utest_this
    out['test1'] = t1
    out['pwatch'] = fnwatch.set_watchers
    out['pfind'] = fsearch.generic_find
    out['pflush'] = _pflush
    out['changes'] = usetrack.get_edits
    out['dunwrap'] = _unwrap # Useful to see the total size of data structure.
    out['help'] = _help
    return out

def splat_here(modulename):
    kvs = cmds1()
    module = sys.modules[modulename]
    for k in kvs.keys():
        module.__dict__[k] = kvs[k]
