# Filters the walking functions.
import sys

# DEBUG CODE:
from Termpylus_UI import slowprint
_sprts = [slowprint.last_impression_print, slowprint.fileprint, slowprint.fileprint1]
_sprt = _sprts[1] # Change this ix to change which one is used.
def sprt(*args):
    _sprt(*args, main_printer=sys.modules['__main__'].print_state_singleton)


def default_blockset(x):
    # Avoid wild goose chases. Returns ids since some objects are unhasable.
    if x is sys.modules['Termpylus_shell.shellpython']:
        # Avoid digging into user variables.
        ok = {'str1','_module_vars','run', 'bashyparse2pystr', 'python', 'py_kwds',
              'numeric_str', 'is_quoted', 'bashy', 'is_pyvar', 'split_by_eq',
              'attempt_shell_parse', 'exc_to_str', 'Shell'}
        return set(x.__dict__.keys())-ok
    else:
        return {}

def override_to_dict1(x, level=0):
    # Overrides the default to_dict_1 behavior, None means to not override.
    # This is applied BEFORE the filtering with the blockset function.
    return None

    sty = str(type(x))
    if "'itertools.count'" in sty:
        print('About to get the dict:')
        print('x is:', x)
        #d = list(x)
        #from . import walk
        #d2 = walk.to_dict1(x)
        print('Done')
        TODO
    return None
