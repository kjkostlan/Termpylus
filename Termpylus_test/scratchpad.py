import sys, random, time
Termpylus_main = sys.modules['__main__']
findme0 = sys.modules['__main__'].GUI.set_shell_output

def some_test(*args): # Call with test1
    from Termpylus_core import dwalk, var_watch, file_io
    from Termpylus_UI import slowprint
    sprt = slowprint.last_impression_print # Shorthand.
    from . import ttools, test_varmodtrack, test_pythonverse, test_parse
    from Termpylus_test import test_shell, test_pyrun
    # Scratchwork tests go here. Reset to 'return True' when git commiting.

    #return test_parse.test_py_fsm()
    #return test_parse.test_py_defs()
    #return test_parse.test_bash2py()
    #return test_parse.test_bash_parse()
    return test_pyrun.test_python_openproject()
    pass
