# TODO: Import lots of modules even those not needed.
from Termpylus_py import walk, fnwatch, mload
from Termpylus_UI import slowprint
import sys, random, time
Termpylus_main = sys.modules['__main__']
sprt = slowprint.last_impression_print # Shorthand.

def some_test(args): # Call with test1
    # Scratchwork tests go here. Reset to 'return True' when git commiting.
    import numpy as np
    #time.sleep(2)

    huge = sys.modules
    #y = walk.owalk(huge, f, combine_f=None, usedset=None, eval_kys=False, blocklist_fn=None)
    huge_dict = walk.to_dict(huge)

    yflat = walk.unwrap(huge_dict)
    #import Termpylus_main
    find_me_f = Termpylus_main.GUI.maybe_send_command
    kys = []
    yfk = list(yflat.keys())
    #for k in yflat.keys():
    #    if yflat
    #ids = walk.ob_key(find_me_f)

    print('Len of the Pythonverse:', len(yfk))
    ixs = random.sample(list(range(len(yfk))), 16)
    return [[yfk[ix], yflat[yfk[ix]], ix] for ix in ixs]
