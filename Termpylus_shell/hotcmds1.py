# More hot commands.
# Functions go here for ease of acess and are avaialbe w/o import.
import sys
from Termpylus_py import usetrack, fsearch, fnwatch

def utest_this(args):
    # Unitests.
    print('**Running unit tests**')
    from Termpylus_test import test_pyrun # Better to not have circular dependencies.
    if not test_pyrun.run_tests():
        return False
    from Termpylus_test import test_shell
    if not test_shell.run_tests():
        return False
    return True

def utest0_this(args):
    # Scratchwork tests go here. Reset to 'return True' when git commiting.
    import Termpylus_test.test_pyrun
    Termpylus_test.test_pyrun.test_py_import0()
    return mload.module_file('smain')

def cmds1():
    #These extra cmds are for python editing.
    # Will add many more...
    out = {}
    out['utest'] = utest_this
    out['utest0'] = utest0_this
    out['pwatch'] = fnwatch.set_watchers
    out['pfind'] = fsearch.generic_find
    out['changes'] = usetrack.get_edits
    return out

def splat_here(modulename):
    kvs = cmds1()
    module = sys.modules[modulename]
    for k in kvs.keys():
        module.__dict__[k] = kvs[k]
