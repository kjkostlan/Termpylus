# When are functions called?
import sys

# Singleton globals only set up once.
try:
    _ = fglobals
except NameError:
    fglobals = dict()
    fglobals['original_fns'] = {} # Name-qual => function.
    fglobals['logs'] = {} # name-qual => inputs-as-dict.

############################ Var mutation watching #############################

def add_logged_var():
    # Vars logged on mutation (how to do this???)
    # (well-written code shouldn't have to hunt down mutations, but should != reality).
    TODO

################################ Fn watching core engine ###################################

def get_callable(modulename, var_name):
    pieces = var_name.split('.')
    TODO

def set_callable(modulename, var_name, f_obj):
    # m.__dict__[var_name] = f but more complex for classes.
    TODO

def logged_fn(modulename, var_name):
    # Makes a logged version of the function, which behaves the same but adds to logs.
    f_obj = get_callable(modulename, var_name)
    def f(_SYM_name=name, *args, **kwargs):
        kwargs1 = kwargs.copy()
        for i in range(len(args)):
            kwargs1[i] = args[i] # Number args turn into dict keys with numerical values.
        if _SYM_name not in fglobals:
            fglobals[_SYM_name] = []
        time0 = time.time()
        out = f_obj(*args, **kwargs)
        kwargs1['_time'] = [time0, time.time()]
        kwargs1['return'] = out # return is a reserved keyword.
        fglobals[_SYM_name].append(kwargs1)
        return out
    return f

def add_fn_watcher(modulename, var_name, f_code=None):
    # Changes the function in var_name to record it's inputs and outputs.
    # Replaces any old watchers.
    # f_code can change the code passed into f.
    m = sys.modules[modulename]
    k = modulename+'.'+var_name
    f_obj = get_callable(modulename, var_name)
    if modified_code is None:
        f_obj1 = fglobals.get('original_fns', f_obj)
    else:
        f_obj1 = eval(f_code) #TODO: eval in right environment.
    f = logged_fn(modulename, var_name, f_obj)

    fglobals['original_fns'][modulename+'.'+var_name] = f_obj
    set_callable(modulename, var_name, f)
    return f

def rm_fn_watcher(modulename, var_name):
    name_qual = modulename+'.'+var_name
    fcache = fglobals['original_fns']
    if name_qual in fcache:
        m = sys.modules[modulename]
        set_callable(modulename, var_name, fcache[name_qual])
        del fcache[name_qual]

################################ Performance heuristics ###################################
# TODO (will only TODO when performance becomes a concern).

################################ Fn watching mass actions ###################################

def list_callables(modulename):
    # Includes nesting for classes!
    TODO

def add_all_watchers():
    # Is this too many?
    #sys.modules[]
    TODO

def with_watcher(modulename, var_name, args):
    TODO

def remove_all_watchers(modulename):
    #sys.modules[]
    TODO

def get_logs(fn_name_qual):
    return fglobals['logs']
    TODO

def remove_all_logs():
    fglobals['logs'] = {}

'''
class Foo():
   def __init__(self, x):
      self.x = x
   def report(self):
      return self.x*3

y = Foo(5)
yr = y.report()
fn = Foo.report
z = fn(Foo(6))
Foo.report = lambda w: w.x*40
yr1 = y.report() # Change in behavior.
y1r = Foo(5).report() # Also change in behavior.

def f0(*args):
    print('Fn no longer alive')
# No change in behavior b/c the maybe_send_command method was already passed to the listeners.
sys.modules['__main__'].GUI.maybe_send_command = f0

'''
