from Termpylus_core import dwalk, var_watch, modules, file_io, strparse
from Termpylus_UI import slowprint
from . import ttools, test_varmodtrack, test_pythonverse
import sys, random, time
Termpylus_main = sys.modules['__main__']
sprt = slowprint.last_impression_print # Shorthand.
findme0 = sys.modules['__main__'].GUI.set_shell_output

def some_test(args): # Call with test1
    # Scratchwork tests go here. Reset to 'return True' when git commiting.
    #return test_varmodtrack.test_var_get()
    #code = file_io.contents('./Termpylus_core/updater.py')
    #defs = strparse.sourcecode_defs(code, nest=True)
    #print('Def keys:', defs.keys())
    return test_pythonverse.search_source_test()
    pass
