# TODO: Import lots of modules even those not needed.
from Termpylus_core import dwalk, var_watch, modules
from Termpylus_UI import slowprint
from . import ttools, test_varmodtrack, test_pythonverse
import sys, random, time
Termpylus_main = sys.modules['__main__']
sprt = slowprint.last_impression_print # Shorthand.
findme0 = sys.modules['__main__'].GUI.set_shell_output

def some_test(args): # Call with test1
    # Scratchwork tests go here. Reset to 'return True' when git commiting.
    #return test_varmodtrack.test_var_get()
    return test_pythonverse.find_gui_fn_test()
    #pass
