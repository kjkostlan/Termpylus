import sys
from . import ttools
from Termpylus_core import dwalk, todict

def test_dict_instanced_function():
    # Conversion to dictionary?
    class_def = sys.modules['__main__'].GUI
    class_inst = sys.modules['__main__'].gui
    dc = todict.to_dict1(class_def, 0)
    di = todict.to_dict1(class_inst, 0)
    k = 'maybe_click_history'
    t0 = (k in dc) and not (k in di) and (hasattr(class_inst, k)) and not (k in class_inst.__dict__) and (k in dir(class_inst))
    return t0
