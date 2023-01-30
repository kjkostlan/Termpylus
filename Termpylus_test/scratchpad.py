# TODO: Import lots of modules even those not needed.
from Termpylus_py import walk, fnwatch, mload
from Termpylus_UI import slowprint
from . import ttools
import sys, random, time
Termpylus_main = sys.modules['__main__']
sprt = slowprint.last_impression_print # Shorthand.
findme0 = sys.modules['__main__'].GUI.set_shell_output

def some_test(args): # Call with test1
    # Scratchwork tests go here. Reset to 'return True' when git commiting.
    #import numpy as np
    #time.sleep(2)

    huge = sys.modules
    #y = walk.owalk(huge, f, combine_f=None, usedset=None, eval_kys=False, blocklist_fn=None)
    huge_dict = walk.to_dict(huge)

    yflat = walk.unwrap(huge_dict)

    #import Termpylus_main
    findme = sys.modules['__main__'].GUI.set_shell_output
    #findme = sys.modules['__main__'].gui.maybe_click_history # Lowercase means a per-instance object.
    findme = sys.modules['__main__'].gui

    p, d1 = walk.find_in(huge_dict, findme)

    print('-------------------------------------')

    #print('d1 keys:', d1.keys(), type(findme))
    #print('d1 keys1:', findme.__dict__.keys(), findme.maybe_click_history)
    #print('Looking for  method:', d1['maybe_click_history'])

    #print('What to find:', findme, 'Tree-splay size', len(yflat))

    #print('Silver in huge dict:', huge_dict['__main__']['gui'])
    #print('Found here:', p, findme)

    out = []
    for k in yflat.keys():
        if yflat[k] is findme:
            out.append(k)
    return out

    gui_kys = []
    for k in yflat.keys():
        if type(k) is str and k.endswith('GUI'):
            gui_kys.append(k)

    out = dict(zip(gui_kys, [yflat[k] for k in gui_kys]))
    ids = [id(x) for x in out.values()]

    treasure_kys = []
    for k in yflat.keys():
        if yflat[k] is findme:
            treasure_kys.append(k)

    #for k in yflat.keys():
    #    if yflat
    #ids = walk.ob_key(find_me_f)
    #print('Len flat:', len(yflat))

    #print('Stuff:', yflat['__main__.GUI'], len(kys))

    return treasure_kys

    #print('Len of the Pythonverse:', len(yfk))
    #ixs = random.sample(list(range(len(yfk))), 16)
    #return [[yfk[ix], yflat[yfk[ix]], ix] for ix in ixs]
