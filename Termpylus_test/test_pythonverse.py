# Tests that need the pythonverse. It is slow to call the pythonverse so it gets reused.
import sys
from Termpylus_core import ppatch, updater, todict, dwalk
from . import ttools

try:
    _pyverse
except:
    _pyverse = [None, None]

def _getpyverse():
    if _pyverse[0] is None or _pyverse[1] is None: # Compute once.
        x = todict.to_dict(sys.modules) # BIG step.
        _pyverse[0] = todict.MysteryHolder(x) # Prevent the dict search on everything from seeing this.
        _pyverse[1] = todict.MysteryHolder(dwalk.unwrap(x))
    return _pyverse[0].val, _pyverse[1].val

def count_test():
    # It has about 30k but only ~150 at top level.
    x, xu = _getpyverse()
    return len(x)<1024 and len(xu)>4096

def find_gui_fn_test():
    # Tkinter *really* swallows things so it is almost impossible to get the function.
#tkinter: Termpylus_test•scratchpad•Termpylus_main•gui•all_widgets•2 .!listbox
#tkinter: Termpylus_test•scratchpad•Termpylus_main•gui•historybox•master .
    fn_ver1 = sys.modules['__main__'].gui.maybe_send_command
    x, xu = _getpyverse()
    #dwiget = x['Termpylus_test']['scratchpad']['Termpylus_main']['gui']['all_widgets'][0]
    #print('Sample type:', type(sys.modules['__main__'].gui.text_input))
    #Obk = todict.ob_key
    #kys = list(dwiget.keys())
    #print('Ob key ids:', Obk, id(Obk), kys[-1], id(kys[-1]))
    #print('Looking:', type(dwiget[Obk]), dwiget.keys(), type(dwiget['master'][Obk]))
    for k in xu.keys():
        if updater.same_inst_method(xu[k], fn_ver1):
            return True
    return False

def run_tests():
    return ttools.run_tests(__name__)