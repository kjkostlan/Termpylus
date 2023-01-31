# Functions to walk dictionaries.


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
