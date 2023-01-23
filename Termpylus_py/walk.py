# Walk across the Pythonverse! Converts datastructures to nested dicts for ease-of-use.
import traceback, sys
from . import walk_filter

try:
    len(debug_strangetypes)
except:
    debug_strangetypes = {}

anti_loop = [0]

class ObKey():
    # Key for the object. Avoids dict collections.
    def __init__(self):
        pass
    def __hash__(self):
        return id(self)
    def __str__(self):
        return '|ob_key|'
ob_key = ObKey()

class CircleHolder():
    # Holds circular dependencies. Stops the recursive search.
    def __init__(self, val, val_as_dict):
        self.val = val
        self.val_as_dict = val_as_dict
    def __str__(self):
        return '⸦'+str(self.val)+'⸧'
    def __repr__(self):
        return '⸦'+str(self.val)+'⸧'

class MysteryHolder():
    # Holds mysteries. These are not expored deeper for performance. Stops the recursive search.
    def __init__(self, val):
        self.val = val
    def __str__(self):
        return '⟅'+str(self.val)+'⟆'
    def __repr__(self):
        return '⟅'+str(self.val)+'⟆'

class Traced():
    # Traces ancestors; used for unwrap. Stops the recursive search (not really needed).
    def __init__(self, val, ancestors):
        self.val = val
        self.line = ancestors.copy()
    def __str__(self):
        return '⦅'+str(self.val)+'⦆'
    def __repr__(self):
        return '⦅'+str(self.val)+'⦆'

##################################Core walking tools############################

def to_dict1(x, level):
    # Converts x to a dict.
    # If x can't be broken down into smaller peices returns None
    # Only one level deep, does not operate recursivly.
    if level>768:
        raise Exception('Infinite recursion depth likely.')

    def finlz(z):
        if hasattr(x,'__defaults__'): # Extracts function info.
            z['__defaults__'] = x.__defaults__
        if anti_loop[0] > 8e5:
            raise Exception('Infinite loop possible (where searching through items creates items ad infinitum), aborted at nest level '+str(level)+'; object: '+str(x))
        return z

    anti_loop[0] = anti_loop[0]+1
    kvs = {}
    ty = type(x)
    ty_txt = str(ty)

    # If this module gets reloaded the 4 holders will be redefined and is will fail. However, the str should still work.
    if ty_txt == str(CircleHolder) or ty_txt == str(MysteryHolder) or ty_txt == str(Traced):
        return None
    elif ty is str: # strs are considered leafs even though they can be iterated.
        return None
    elif ty is dict:
        return x.copy()
    elif ty is set:
        return finlz(dict(zip(x,x)))
    elif hasattr(x, '__dict__'): # objects (classes, types, modules)
        dc = x.__dict__
        strd = str(type(dc))
        debug_strangetypes[strd] = x
        #print('Type of dict:', str(type(x.__dict__)))
        #print('Reg keys:', debug_strangetypes)
        if type(dc) is not dict: # Actually a mapping proxy.
            return finlz(dict(zip(dc.keys(), dc.values())))
        else:
            return finlz(dc.copy())
    elif ty is list or ty is tuple:
        return dict(zip(range(len(x)), x))
    #elif hasattr(x,'__iter__'): # Too many infinite iterators.
    #    try:
    #        x1 = list(x)
    #    except TypeError: # occasionally this fails.
    #        return None
    #    #sprt('__iter__ on:', type(x))
    #    out = finlz(dict(zip(range(len(x1)),x1)))
    #    #sprt('done with __iter__ on:', type(x))
    #    return out
    else:
        return None

def dfilter(d, useddict=None, blockset=None):
    # Useddict accumilates object ids and prevents circular refrences.
    # Blockset is an extra set that we don't use.
    if d is None:
        return d
    if useddict is None:
        useddict = dict()
    if blockset is None:
        blockset = set()
    d1 = d.copy()
    for k in list(d.keys()):
        idi = id(d1[k])
        if idi in blockset:
            d1[k] = MysteryHolder(d1[k])
        elif idi in useddict and useddict[idi] is not None: #Only circlehold non-None dicts.
            d1[k] = CircleHolder(d1[k], useddict[idi])
    return d1

def is_leaf_type(x):
    return to_dict(x) is None

################################# Recursive functions ##########################

def to_dict(x, useddict=None, blockset_fn=walk_filter.default_blockset, d1_override=walk_filter.override_to_dict1, level=0):

    if useddict is None:
        useddict = dict()
    #sprt('Before dict1:', str(type(x)))
    if d1_override is not None:
        y = d1_override(x, level)
    if y is None:
        y = to_dict1(x, level)
    useddict[id(x)] = y
    #sprt('After dict1:', str(type(x)))

    if y is None:
        return x
    if blockset_fn is None:
        blockset_fn = lambda x:set()

    z = dfilter(y, useddict=useddict, blockset=blockset_fn(x))

    zk = sorted(list(z.keys()), key=str) # Sort for determinism.
    for k in zk:
        if str(type(k))==str(ObKey):
            pass
        z[k] = to_dict(z[k], useddict, blockset_fn, d1_override, level+1)

    z[ob_key] = x
    return z

def dwalk(d, f, combine_f=None, combine_g=None):
    # Dict walk. Use to_dict first.
    # Combinef = within the layer.
    # Combineg = upper, lower layer. If none defaults to combine_f with two keys.
    if type(d) is dict:
        d1 = d.copy()
        for k in d.keys():
            d1[k] = dwalk(d1[k],f, combine_f)
        if combine_f is not None:
            d2 = combine_f(d1)
            if combine_g is not None:
                return combine_g(d, d2)
            else:
                return combine_f({'_upper':d, '_lower':d2})
        else:
            return f(d1)
    else:
        return f(d)

def unwrap(d, head='', ancestry=None):
    # Unwraps the dict d using '.' to seperate recursive keys.
    # Each dict key is a path.
    kys = sorted(list(d.keys()), key=str) # Sort for determinism.
    if ancestry is None:
        ancestry = []
    out = {}
    for k in kys:
        if type(d[k]) is dict and str(type(k)) != str(ObKey):
            out = {**out, **unwrap(d[k],head+str(k)+'.', ancestry+[d])}
        else:
            ty_txt = str(type(d[k]))
            if ty_txt == str(CircleHolder) or ty_txt == str(MysteryHolder) or ty_txt == str(Traced):
                v = d[k].val # Splice these holders.
            else:
                v = d[k]
            out[head+str(k)] = Traced(d[k], ancestry)
    return out
