# Patch system: Allows making and removing patches to variables.
import sys
from . import gl_data

if 'ppaglobals' not in gl_data.dataset:
    # Name-qual => function; name-qual => inputs-as-dict.
    gl_data.dataset['ppaglobals'] = {'original_fnss':{}}
_gld = gl_data.dataset['ppaglobals']

def get_var(modulename, var_name):
    # Gets the f_object.
    pieces = var_name.split('.')
    TODO

def set_var(modulename, var_name, x):
    # m.__dict__[var_name] = x but more complex for classes.
    _gld['original_fnss'][modulename][var_name] = get_var(modulename, var_name)
    TODO

def remove_patch(modulename, var_name):
    TODO

def _get_vars_core(out, x, subpath, nest, usedids):
    d = x.__dict__ # Found in both modules and classes.
    for k in d.keys():
        if id(d[k]) in usedids:
            continue # Avoids infinite loops with circular class references.
        if k.startswith('__') and k.endswith('__'): # Oddball python stuff we do not need.
            continue
        out[subpath+k] = d[k]
        usedids.add(id(d[k]))
        if nest and type(d[k]) is type: # Classes.
            _get_vars_core(out, d[k], subpath+k+'.', nest, usedids)

def get_vars(modulename, nest_inside_classes=True):
    # Map from symbol to name.
    out = {}
    usedids = set()
    x = sys.modules[modulename]
    _get_vars_core(out, x, '', nest_inside_classes, usedids)
    return out

def get_all_vars(nest_inside_classes=True):
    TODO