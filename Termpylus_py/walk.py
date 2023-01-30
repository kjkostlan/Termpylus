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
        return '⟮ob_key⟯'
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

    # If this module gets reloaded the 4 holders will be redefined and 'is' will fail. However, the str should still work.
    if ty_txt == str(CircleHolder) or ty_txt == str(MysteryHolder):
        return None
    elif ty in {str, float, int}:
        return None # These are considered leaf types.
    elif ty is dict:
        return x.copy()
    elif ty is set:
        return finlz(dict(zip(x,x)))
    elif ty is list or ty is tuple:
        return dict(zip(range(len(x)), x))
    elif hasattr(x,'__dict__'):
        # Class instance methods are hard to look up:
        # https://stackoverflow.com/questions/62105974/do-objects-have-a-copy-of-their-class-methods
        return finlz(x.__dict__.copy())
    else:
        return None


def mark_blocked(d, useddict=None, blockset=None, removeset=None):
    # Useddict accumilates object ids and prevents circular refrences.
    # Blockset is an extra set that we don't use.
    if d is None:
        return d
    if useddict is None:
        useddict = dict()
    if blockset is None:
        blockset = set()
    if removeset is None:
        removeset = set()
    d1 = d.copy()
    for k in list(d.keys()):
        idi = id(d1[k])
        if k in blockset:
            d1[k] = MysteryHolder(d1[k])
        elif k in removeset:
            del d1[k]
        elif idi in useddict and useddict[idi] is not None: #Only circlehold non-None dicts.
            if str(type(d1[k])) == str(CircleHolder):
                raise Exception('Nested circleholder.')
            d1[k] = CircleHolder(d1[k], useddict[idi])
    return d1

def is_leaf_type(x):
    return to_dict(x) is None

################################# Recursive functions ##########################

def to_dict(x, useddict=None, blockset_fn=walk_filter.default_blockset, removeset_fn=walk_filter.default_no_showset, d1_override=walk_filter.default_override_to_dict1, level=0):
    if useddict is None:
        useddict = dict()
    #sprt('Before dict1:', str(type(x)))
    if d1_override is not None:
        y = d1_override(x, level)
    if y is None:
        y = to_dict1(x, level)

    useddict[id(x)] = x
    #sprt('After dict1:', str(type(x)))

    if y is None:
        return x
    if blockset_fn is None:
        blockset_fn = lambda x,kys:set()

    z = mark_blocked(y, useddict=useddict, removeset=removeset_fn(x, list(y.keys())), blockset=blockset_fn(x, list(y.keys())))

    zk = sorted(list(z.keys()), key=str) # Sort for determinism.
    for k in zk:
        if str(type(k))==str(ObKey):
            continue
        if level>745:
            _deeper = to_dict1(z[k], level+1)
            if _deeper is not None and k in _deeper:
                print('Likely infinite loop; key is:', k, 'x is:', [x, z[k]], 'ID:', id(x),'Level:', level)
        z[k] = to_dict(z[k], useddict, blockset_fn, removeset_fn, d1_override, level+1)
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

def _unwrap_core(d, head, ancestry):
    out = {}
    kys = sorted(list(d.keys()), key=str) # Sort for determinism.

    for k in kys:
        if type(d[k]) is dict and str(type(k)) != str(ObKey):
            out = {**out, **unwrap(d[k],head+str(k)+'•', ancestry+[d])}
        else:
            out[head+str(k)] = d[k]
    return out

def _splice_core(d):
    d = d.copy()
    for k, v in d.items():
        ty_txt = str(type(v))
        if ty_txt == str(CircleHolder) or ty_txt == str(MysteryHolder):
            d[k] = v.val
            ty_txt = str(type(v.val))
            if ty_txt == str(CircleHolder) or ty_txt == str(MysteryHolder):
                raise Exception('Nested holders.')
    # Remove the ObKey tails from each key:
    txt = '•'+str(ob_key)
    return dict(zip([k.replace(txt, '') for k in d.keys()], d.values()))

def unwrap(d, head='', ancestry=None):
    # Unwraps the dict d using '•' as a path delim.
    # Mostly a debug tool.
    if ancestry is None:
        ancestry = []
    d = _unwrap_core(d, head, ancestry)
    d = _splice_core(d)
    return d


def get_in(x, ks):
    if len(ks)==0:
        return x
    if ks[0] not in x:
        return None
    return get_in(x, ks[1:])

def find_in(d, x, prepend=None):
    # Returns the path to object x and enclosing dict in nested dict d.
    # There will be exactly one path if it is successful since CircleHolders don't count.
    if prepend is None:
        prepend = []
    if ob_key in d and d[ob_key] is x:
        return prepend, d
    for k in d.keys():
        if k is not ob_key and type(d[k]) is dict:
            p, y = find_in(d[k], x, prepend+[k])
            if p is not None:
                return p, y
    return None, None
