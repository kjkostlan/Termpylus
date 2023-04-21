# Tests that need the pythonverse. It is slow to call the pythonverse so it gets reused.
import sys
from Termpylus_core import updater, todict, dwalk, dquery, file_io, gl_data
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
    #TODO # Test src edit.
    #xw1 = dquery.source_find('-n1', 'dui', '-ar12', 20, '-precompute',1)
    #return False
    out = True

    try:
        dquery.source_find('-badopt', 10)
        out = False
    except:
        pass
    xn = dquery.source_find('-n', 'gui_fn_test', '-precompute',1); out = out and 'find_gui_fn_test' in str(xn)
    xar = dquery.source_find('-ar','20', '-precompute',1); out = out and 'todict.to_dict' in str(xar)
    xar = bashy_cmds.sfind(['-ar', '20', '-precompute',1], None); out = out and 'todict.to_dict' in str(xar) # Equivalent version for in the command prompt.
    xarv = dquery.source_find('-ar', 0, '-returnsrcv', 1, '-precompute',1); out = out and 'Sourcevar' in str(xarv)
    xs = dquery.source_find('-s', "if fname not in fglobals['original_txts']", '-precompute',1); out = out and 'contents_on_first_call' in str(xs)
    xw1 = dquery.source_find('-n1', 'GUI', '-ar12', 20, '-precompute',1)
    xw2 = dquery.source_find('-n12', 'GUI', '-ar1', 20, '-precompute',1)
    out = out and str(xw1).count('GUI')<str(xw2).count('GUI')

    #print('Pieces:', 'find_gui_fn_test' in str(xn), 'todict.to_dict' in str(xar), 'Sourcevar' in str(xarv), len(xarv)>96, 'contents_on_first_call' in str(xs))
    fname = './Termpylus_test/changeme.py'
    old_txt = '_Baz123_'
    new_txt = '_Bets123_'
    file_io.fsave(fname, file_io.contents(fname).replace(new_txt, old_txt))
    gl_data.dataset['fileio_globals']['original_txts'] = {}; print('Wiped out file_globals original txt for testing') # Wipe this out.
    xch0 = dquery.source_find('-ed', 1.0); out = out and len(xch0)==0
    file_io.fsave(fname, file_io.contents(fname).replace(old_txt, new_txt))
    xch1 = dquery.source_find('-ed', 1.0); out = out and 'see_changes_here' in str(xch1)
    file_io.fsave(fname, file_io.contents(fname).replace(new_txt, old_txt))

    print('Stuff:', xch0)
    return False

    TODO # Test logging as well.

    if not out:
        print('This test is subject to breaking since it makes assumptions about the code.')
    return out

def run_tests():
    return ttools.run_tests(__name__)
