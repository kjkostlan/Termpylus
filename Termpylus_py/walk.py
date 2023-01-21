# Walk across the Pythonverse! Converts datastructures to nested dicts for ease-of-use.
import traceback, sys

'''
# How to find default args:
def foo(x=[1,2,3]):
  return x[0]
y = foo.__defaults__
y[0][0] = 123
z = foo()
'''
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

class ObHolder():
    # Holds the original object. Stops the recursive search.
    def __init__(self, val):
        self.val = val
    def __str__(self):
        return '❮'+str(self.val)+'❯'
    def __repr__(self):
        return '❮'+str(self.val)+'❯'

class CircleHolder():
    # Holds circular dependencies. Stops the recursive search.
    def __init__(self, val):
        self.val = val
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

def default_blockset(x):
    # Avoid wild goose chases. Returns ids since some objects are unhasable.
    if type(x) is module and x is sys.modules['Termpylus_shell.shellpython']:
        # Avoid digging into user variables.
        ok = {'str1','_module_vars','run', 'bashyparse2pystr', 'python', 'py_kwds',
              'numeric_str', 'is_quoted', 'bashy', 'is_pyvar', 'split_by_eq', 
              'attempt_shell_parse', 'exc_to_str', 'Shell'}
        return set(x.__dict__.keys())-ok
    else:
        return {}

##################################Core walking tools############################

def to_dict1(x, level):
    # Converts something to x. usedset blocks circular references and is full of ids.
    # Leafs become None (and are later replaced by the object itself)
    # Only one level deep, does not operate recursivly.
    if level>768:
        raise Exception('Infinite recursion depth likely.')

    def finlz(z):
        if hasattr(x,'__defaults__'): # Extracts function info.
            z['__defaults__'] = x.__defaults__
        if anti_loop[0] > 8e5:
            #print('Are we a showstopper:', str(ty), [str(ObHolder), str(CircleHolder)], [ty is ObHolder, ty is CircleHolder])
            raise Exception('Infinite loop possible, aborted at nest level '+str(level)+'; object: '+str(x))
        return z

    anti_loop[0] = anti_loop[0]+1
    kvs = {}
    ty = type(x)
    ty_txt = str(ty)

    # If this module gets reloaded the 4 holders will be redefined and is will fail. However, the str should still work.
    if ty_txt == str(ObHolder) or ty_txt == str(CircleHolder) or ty_txt == str(MysteryHolder) or ty_txt == str(Traced):
        return None
    elif hasattr(x, '__dict__'): # objects (classes, types, modules)
        dc = x.__dict__
        strd = str(type(x.__dict__))
        debug_strangetypes[strd] = x
        #print('Type of dict:', str(type(x.__dict__)))
        #print('Reg keys:', debug_strangetypes)
        if type(dc) is not dict: # Actually a mapping proxy.
            return finlz(dict(zip(dc.keys(), dc.values())))
        else:
            return finlz(dc.copy())
    elif type(x) is str: # strs are considered leafs even though they can be iterated.
        return None
    elif ty is dict:
        return x
    elif ty is set:
        return finlz(dict(zip(x,x)))
    elif hasattr(x,'__iter__'):
        x1 = list(x)
        return finlz(dict(zip(range(len(x1)),x1)))
    else:
        return None
    if out is None:
        return out
    if out is None or blocklist_fn is None:
        return out

def dfilter(d, usedset=None, blockset=None):
    # Usedset accumilates object ids and prevents circular refrences.
    # Blockset is an extra set that we don't use.
    if d is None:
        return d
    if usedset is None:
        usedset = set()
    if blockset is None:
        blockset = set()
    d1 = d.copy()
    for k in list(d.keys()):
        idi = id(d1[k])
        if idi in blockset:
            d1[k] = MysteryHolder(d1[k])
        elif idi in usedset and (to_dict1(d1[k], 0) is not None): #Only circlehold non-None dicts.
            d1[k] = CircleHolder(d1[k])
        else:
            usedset.add(idi)
    return d1

def is_leaf_type(x):
    return to_dict(x) is None

################################# Recursive functions ##########################

def to_dict(x, usedset=None, blockset_fn=default_blockset, level=0):
    if usedset is None:
        usedset = set()
    y = to_dict1(x, level)
    if y is None:
        return x
    if blockset_fn is None:
        blockset_fn = lambda x:set()
    z = dfilter(y, usedset=usedset, blockset=blockset_fn(x))
    zk = sorted(list(z.keys()), key=str) # Sort for determinism.
    for k in zk:
        if str(type(k))==str(ObKey):
            pass
        z[k] = to_dict(z[k], usedset, blockset_fn, level+1)
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
    # Each dict value is an
    kys = sorted(list(d.keys()), key=str) # Sort for determinism.
    if ancestry is None:
        ancestry = []
    out = {}
    for k in kys:
        if type(d[k]) is dict and str(type(k)) != str(ObKey):
            out = {**out, **unwrap(d[k],head+str(k)+'.', ancestry+[d])}
        else:
            ty_txt = str(type(d[k]))
            if ty_txt == str(ObHolder) or ty_txt == str(CircleHolder) or ty_txt == str(MysteryHolder) or ty_txt == str(Traced):
                # Splice these holders.
                v = d[k].val
            else:
                v = d[k]
            out[head+str(k)] = Traced(d[k], ancestry)
    return out