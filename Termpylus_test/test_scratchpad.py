# TODO: Import lots of modules even those not needed.
from Termpylus_py import walk
import sys

def some_test(args): # Call with test1
    # Scratchwork tests go here. Reset to 'return True' when git commiting.
    '''
    _ans = dunwrap(test1([]))
    ix = 123
    ky = list(_ans.keys())[ix]
    y = [len(_ans), ky, _ans[ky]]
    '''
    print('All vars in all modules?')
    def f(x):
        return x
    huge = sys.modules
    #y = walk.owalk(huge, f, combine_f=None, usedset=None, eval_kys=False, blocklist_fn=None)
    y = walk.to_dict(huge, usedset=None, blockset_fn=None)
    return y

