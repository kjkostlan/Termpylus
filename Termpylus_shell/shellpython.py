# Python shell with some wrappers for simple linux commands.
# It holds a current working directory to feel shell-like.
import sys, re, importlib, traceback, subprocess
from . import bashy_cmds, bash2py
from Termpylus_extern.waterworks import file_io, modules
from Termpylus_extern.fastatine import bash_parse
from Termpylus_extern.slitherlisp import ppatch

def str1(x):
    sx = str(x)
    if len(sx)>65536:
        sx = '<big thing>'
    return sx

def _module_vars():
    modl = sys.modules[__name__]
    return modl.__dict__.copy()

class Closure():
    # Don't like Pythons "sticky" closures? Use this instead!
    # (Is there a better way than this class)?
    def __init__(self, f, fname, closed_over, g):
        self.closed_over = closed_over
        self.fname = fname
        self.f = f; self.g = g
    def call(self, *args, **kwargs):
        return self.f(*args, **kwargs)
    def get_f(self):
        # No sticky when class methods dynamically make themselves!
        f1 = self.g(self.f, self.closed_over)
        def f2(*args, **kwargs):
            try:
                return f1(*args,**kwargs)
            except Exception as e:
                #txt = repr(e)
                import traceback
                traceback.print_exception(e)
                raise Exception('Bash cmd error in '+self.fname+'. Trace printed to print().') from e
        return f2

################################ Print out fns #################################

def exc_to_str(e):
    # Includes stack trace.
    err = str(repr(e))
    tr = traceback.format_exc()
    lines = tr.split('\n')
    mod_ix = -1
    for i in range(len(lines)): # Remove the head part of the trace.
        if 'in <module>' in lines[i]:
            mod_ix = i
    if mod_ix>-1:
        lines = lines[mod_ix:]
    lines[0] = lines[0].replace('File "<string>"','Commandbox').replace('in <module>','').strip()
    return (err+'\nTraceback:\n'+'\n'.join(lines)).strip()

def simple_assigned_vars(txt):
    # Which vars are assigned with an = sign?
    # Not fool-proof, but should cover most cases.
    lines = txt.replace(';','\n').split('\n')
    vars = []
    lines = txt.split('\n')
    for line in lines:
        pieces = line.split('=')
        if len(pieces)>1:
            vs = pieces[0].split(',') # i.e.  x, y = 1, 2
            for v in vs:
                vars.append(v.strip())
    return vars

def vdif_report(vars0, vars1, the_input, err):
    assigned_list = simple_assigned_vars(the_input)
    n_change = 0
    report_list = []

    changed = set()
    for ky in vars1.keys():
        if vars1[ky] is not vars0.get(ky, None) and str(vars1[ky]) != str(vars0.get(ky, None)):
            changed.add(ky)
    def rep(v):
        if v in vars1:
            if v in changed:
                report_list.append(str(v)+' = '+str1(vars1[v]))
            else:
                report_list.append('('+str(v)+' = '+str1(vars1[v])+')')
    for v in assigned_list:
        if not v.startswith('_'):
            rep(v)
    for ch in changed:
        if not ch.startswith('_') and ch not in assigned_list:
            rep(ch)

    lines = the_input.strip().split('\n') # Allow a simple repeat of a var as the last line.
    if len(lines)>0:
        l1 = lines[-1].replace(';','').strip()
        if l1.startswith('_') and l1 in vars1:
            rep(l1)

    if len(changed)==0 and len(err)==0:
        report_list = report_list+['Command succeeded, no vars changed']
    var_str = '\n'.join(report_list)
    return var_str

################################ The core shell ################################

class Shell:
    def __init__(self):

        self.cur_dir = '.' #TODO: default directory.
        self.outputs = [] # [message, is_error, input_ix]
        self.input_ix = 0
        self.last_err = None # stderr.
        self.listenerf = None

    def autocorrect(self, the_input):
        return bash2py.maybe_bash2py_console_input(the_input)

    def make_module_closures(self):
        # "considered evil" zone ahead: we add properties to the parent module
        # so that they can be used without qualifications in the command line.
        # (due to the need to closure over self we can't use from ... import *)
        bash_parse.add_bash_syntax_fns(__name__)
        us = sys.modules[__name__]
        mname = 'Termpylus_shell.bashy_cmds'; m = sys.modules[mname]
        kys = ppatch.get_vars(mname)

        def g(f, shell):
            def f1(*args):
                return f(args, shell)
            return f1
        for fn_name in kys:
            c = Closure(m.__dict__[fn_name], mname+'.'+fn_name, self, g)
            setattr(us, fn_name, c.get_f())

    def send(self, the_input, include_newline=True):
        self.cur_dir = file_io.abs_path(self.cur_dir).replace('\\','/')
        the_input = the_input.strip()
        if len(the_input)>0:
            self.make_module_closures()

            vars0 = _module_vars()
            err = ''
            try:
                #https://stackoverflow.com/questions/23168282/setting-variables-with-exec-inside-a-function
                exec(the_input, globals(), globals())
            except Exception as e:
                err = exc_to_str(e)

            vars1 = _module_vars()

            var_str = vdif_report(vars0, vars1, the_input, err)

            if len(var_str)>0:
                self.outputs.append([var_str, False, self.input_ix])
            if len(err)>0:
                self.outputs.append([err, True, self.input_ix])

            self.listenerf() #Trigger it manually (since there is no IO stream).
            self.input_ix = self.input_ix+1

    def exit_shell(self):
        pass

    def clear_printouts(self):
        # Clear the shell printouts.
        self.outputs = []

    def add_update_listener(self, f, dt=0.0625):
        self.listenerf = f
