# Tests variable modifications and tracking.
import sys
from Termpylus_core import ppatch, updater
from . import ttools

def test_var_get():
    # Basic test for variable getting.
    v0_gold = sys.modules['Termpylus_core.updater'].save_py_file
    v0_green = ppatch.get_var('Termpylus_core.updater', 'save_py_file')
    if v0_gold is not v0_green:
        return False

    v0_gold = sys.modules['Termpylus_shell.shellpython'].Shell.exit_shell
    v0_green = ppatch.get_var('Termpylus_shell.shellpython', 'Shell.exit_shell')
    if v0_gold is not v0_green:
        return False
    return True

def test_var_set():
    from Termpylus_core import dquery # make sure its loaded.
    modulevarname = ['Termpylus_core.dquery', 'leaf_match']
    v0 = ppatch.get_var(*modulevarname)
    test0 = not ppatch.is_modified(*modulevarname)
    otest0 = ppatch.original_var(*modulevarname) is v0
    x = [0]
    def new_value(y):
        x[0] = 2*y
    ppatch.set_var(*(modulevarname+[new_value]))
    v1 = ppatch.get_var(*modulevarname)
    v1(12)
    test1 = x[0]==24
    test2 = v1 is not v0
    otest1 = ppatch.original_var(*modulevarname) is v0
    test3 = ppatch.is_modified(*modulevarname)

    ppatch.reset_var(*modulevarname)
    v0_1 = ppatch.get_var(*modulevarname)
    test4 = v0 is v0_1
    otest2 = ppatch.original_var(*modulevarname) is v0

    return test0 and test1 and test2 and test3 and test4 and otest0 and otest1 and otest2

def test_get_vars():
    # Tests module-level and global getting all vars.
    v_with_nest = ppatch.get_vars('Termpylus_shell.shellpython', nest_inside_classes=True)
    v_without_nest = ppatch.get_vars('Termpylus_shell.shellpython', nest_inside_classes=False)
    test0 = 'Shell.clear_printouts' in v_with_nest and 'Shell' in v_with_nest and 'sys' not in v_with_nest
    test1 = 'Shell.clear_printouts' not in v_without_nest
    test2 = len(set(v_without_nest.keys())-set(v_with_nest.keys())) == 0
    return test0 and test1 and test2

def test_instance_method():
    # foo.bar will make a fresh bar every time. Can all the different bars be tracked to the same foo?
    class Foo():
        def __init__(self, bar):
            self.bar = bar
        def method1(self):
            return str(self.bar)*4

    foo1 = Foo(1)
    foo2 = Foo(2)
    fn1_0 = foo1.method1
    fn1_1 = foo1.method1
    fn2 = foo2.method1
    fn0 = Foo.method1

    test0 = fn1_0 is not fn1_1
    test1 = updater.same_inst_method(fn1_0, fn1_1)
    test2 = not updater.same_inst_method(fn0, fn1_0)
    test3 = not updater.same_inst_method(fn1_0, fn2)

    return test0 and test1 and test2 and test3

def run_tests():
    return ttools.run_tests(__name__)