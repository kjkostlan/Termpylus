# TODO: Import lots of modules even those not needed.
from Termpylus_py import walk, fnwatch
import sys
Termpylus_main = sys.modules['__main__']

def some_test(args): # Call with test1
    # Scratchwork tests go here. Reset to 'return True' when git commiting.
    modulename = '__main__'
    vmap = fnwatch.get_vars(modulename, nest_inside_classes=True)
    #TODO
    return vmap.keys()

    '''
x = test1([])
x1 = x[1]
if hasattr(x1, 'val'):
  x1v = x1.val
  if hasattr(x1v, 'val'):
    x1vv = x1v.val
    '''
    print('All vars in all modules?')
    def f(x):
        return x
    huge = sys.modules
    #y = walk.owalk(huge, f, combine_f=None, usedset=None, eval_kys=False, blocklist_fn=None)
    huge_dict = walk.to_dict(huge, usedset=None, blockset_fn=None)
    yflat = walk.unwrap(huge_dict)
    #import Termpylus_main
    find_me_f = Termpylus_main.GUI.maybe_send_command
    kys = []
    yfk = list(yflat.keys())
    #for k in yflat.keys():
    #    if yflat
    #ids = walk.ob_key(find_me_f)
    ix = 12345
    return [yfk[ix], yflat[yfk[ix]], len(yfk)]

