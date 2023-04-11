# Python shell with some wrappers for simple linux commands.
# It holds a current working directory to feel shell-like.
import sys, re, importlib, traceback, subprocess
from . import bashy_cmds
from Termpylus_core import file_io
from Termpylus_lang import modules, bashparse, ppatch

# Extra imports to make the command line easier to use:
from Termpylus_core import *
from Termpylus_shell import *
from Termpylus_test import *
from Termpylus_UI import *
from Termpylus_lang import *

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

################################ Running bash commands #########################

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

class Shell:
    def __init__(self):

        self.cur_dir = '.' #TODO: default directory.
        self.outputs = [] # [message, is_error, input_ix]
        self.input_ix = 0
        self.last_err = None # stderr.
        self.listenerf = None

    def autocorrect(self, input):
        return bashparse.maybe_bash2py_console_input(input)

    def make_module_closures(self):
        # "considered evil" zone ahead: we add properties to the parent module
        # so that they can be used without qualifications in the command line.
        # (due to the need to closure over self we can't use from ... import *)
        bashparse.add_bash_syntax_fns(__name__)
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

    def send(self, input, include_newline=True):
        self.cur_dir = file_io.termp_abs_path(self.cur_dir).replace('\\','/')
        input = input.strip()
        if len(input)>0:
            self.make_module_closures()

            vars0 = _module_vars()
            err = ''
            try:
                #https://stackoverflow.com/questions/23168282/setting-variables-with-exec-inside-a-function
                exec(input, globals(), globals())
                #print('Exed input:', input, 'dict:', sys.modules[__name__].__dict__.keys())
            except Exception as e:
                err = exc_to_str(e)

            vars1 = _module_vars()
            new_vars = []
            for ky in vars1.keys():
                if vars1[ky] is not vars0.get(ky, None):
                    if str(vars1[ky]) != str(vars0.get(ky, None)):
                        new_vars.append(str(ky)+' = '+str1(vars1[ky]))
            if len(new_vars)==0 and len(err)==0:
                new_vars = ['Command succeeded, no vars changed']
            var_str = '\n'.join(new_vars)

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
