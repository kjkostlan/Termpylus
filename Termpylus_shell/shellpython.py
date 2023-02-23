# Python shell with some wrappers for simple linux commands.
# It holds a current working directory to feel shell-like.
import sys, re, os, importlib, traceback, subprocess
from . import pybashlib, hotcmds1
from Termpylus_core import updater
from Termpylus_lang import modules, bashparse

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

################################ Running bash commands #########################

pybashlib.splat_here(__name__)
hotcmds1.splat_here(__name__)

def run(cmd, cmd_args):
    # Single-shot run, returns result and sets last_run_err
    # https://stackoverflow.com/questions/89228/how-do-i-execute-a-program-or-call-a-system-command
    dir = pybashlib.absolute_path('.') # Cd to this, which depends on the global singleton shell.
    #https://stackoverflow.com/questions/17742789/running-multiple-bash-commands-with-subprocess
    cmd = 'cd '+dir+'\n'+cmd+' '+' '.join(cmd_args)
    #result = subprocess.run([cmd]+cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    x = '/bin/bash'
    if os.name == 'nt':
        x = 'cmd'
    process = subprocess.Popen(x, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = process.communicate(cmd)

    out = result.stdout.decode('utf-8')
    err = result.edterr.decode('utf-8')
    return out, err

#################################Binding to Python##############################

def python(args):
    # Runs a Python file much like a bash python command, except that it is ran in the current process.
    # What does this mean?
    # The file's folder is taken to be in the root of said python project (TODO: allow other options).
    # This root folder is prepended to sys.path, so that all imports within the project can work.
    # Our module names will almost certanly not conflict with the project.
    # However, multible projects may generate namespace collisions.
    #    I.e. if boh projects have a folder called 'extern'.
    #    (thus it is not recommended to work on multible projects, unless you decollide them).

    P = pybashlib.option_parse(args, ['-m']); fl = set(P['flags']); kv = P['pairs']; x = P['tail'] # kv is empty
    if len(x)==0:
        raise Exception('Must specify filename to run.')
    pyfname = pybashlib.absolute_path(x[0])
    if not pyfname.endswith('.py') and not pyfname.endswith('.txt'):
        pyfname = pyfname+'.py'

    if '-m' in kv:
        modulename = kv['-m']
    else: # Assume we are calling the root module name.
        leaf = pyfname.split('/')[-1]
        modulename = leaf.split('.')[0] # Remove the extension if any.

    folder_name = os.path.dirname(pyfname)
    modules.add_to_path(folder_name)
    foo = modules.module_from_file(modulename, pyfname)

    if '-rmph' in fl: # Remove path (don't make permement changes to path).
        modules.pop_from_path()

    return foo

#################################Determining if bash############################

################################################################################

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
        self.listenerf = None

    def autocorrect(self, input):
        py_vars = set(sys.modules[__name__].__dict__.keys())
        return bashparse.bash2py_autocorrect(input, py_vars)

    def send(self, input, include_newline=True):
        self.cur_dir = os.path.realpath(self.cur_dir).replace('\\','/')
        input = input.strip()
        if len(input)>0:
            pybashlib.shell = self # So that fns from pybashlib work properly.

            updater.update_user_changed_modules() # Update modules.
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
