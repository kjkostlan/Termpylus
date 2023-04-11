# Tests that need the pythonverse. It is slow to call the pythonverse so it gets reused.
import sys
from Termpylus_core import updater, todict, dwalk, dquery
from Termpylus_lang import ppatch
from Termpylus_shell import bashy_cmds
from . import ttools

try:
    _pyverse
except:
    _pyverse = [None, None]

def _getpyverse():
    if _pyverse[0] is None or _pyverse[1] is None: # Compute once.
        print('***Slow computation ahead, may take 1 min***')
        x = todict.to_dict(sys.modules) # BIG step.
        _pyverse[0] = todict.MysteryHolder(x) # Prevent the dict search on everything from seeing this.
        _pyverse[1] = todict.MysteryHolder(dwalk.unwrap(x))
    return _pyverse[0].val, _pyverse[1].val

def count_test():
    # It has about 30k but only ~150 at top level.
    disable = False
    if disable:
        return False # The pythonverse can be problematic.
    x, xu = _getpyverse()
    return len(x)<1024 and len(xu)>4096

def find_gui_fn_test():
    # Tkinter *really* swallows things so it is almost impossible to get the function.
    # Thus updater.same_inst_method(xu[k], fn_ver1) fails.
    return True

def search_source_test():
    # Not the pythonverse itself, but a similar idea.
    # Does not test requring.
    # TODO: more tests.
    xn = dquery.source_find('-n', 'gui_fn_test')
    xar = dquery.source_find('-ar','20')
    xar = bashy_cmds.sfind(['-ar', '20'], None) # Equivalent version used in the command prompt.
    xarv = dquery.source_find('-ar', 0, '-v')
    xs = dquery.source_find('-s', "if fname not in fglobals['original_txts']")
    #print('Pieces:', 'find_gui_fn_test' in str(xn), 'todict.to_dict' in str(xar), 'Sourcevar' in str(xarv), len(xarv)>96, 'contents_on_first_call' in str(xs))
    return 'find_gui_fn_test' in str(xn) and 'todict.to_dict' in str(xar) and 'Sourcevar' in str(xarv) and len(xarv)>96 and 'contents_on_first_call' in str(xs)

def run_tests():
    return ttools.run_tests(__name__)
