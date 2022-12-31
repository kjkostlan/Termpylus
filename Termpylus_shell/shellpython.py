# Python shell with some wrappers for simple linux commands.
# It holds a current working directory to feel shell-like.
import sys, re, os, importlib, traceback
from . import pybashlib

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
    out, err = process.communicate(commands)

    out = result.stdout.decode('utf-8')
    err = result.edterr.decode('utf-8')
    return out, err

def bashyparse2pystr(out_var, cmd, args):
    # Equivalent python command.
    cmd_builtin = True # TODO: turn false when shell.
    if cmd not in pybashlib.top_25():
        cmd_builtin = False
    def quote_if_needed(x):
        if '"' in x or "'" in x:
            return x
        return '"'+x+'"'

    arg_str = '['+','.join([quote_if_needed(a) for a in args])+']'
    if not cmd_builtin:
        return '%s, _err = run("%s", %s)'%(str(out_var), str(cmd), arg_str)
    else:
        return '%s = %s(%s)'%(str(out_var), str(cmd), arg_str)

#################################Binding to Python##############################


def python(args):
    # Runs python, but in the same python process (i.e it does not run another python program in the terminal).
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

    #https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
    spec = importlib.util.spec_from_file_location(modulename, pyfname)
    foo = importlib.util.module_from_spec(spec)
    sys.modules[modulename] = foo
    spec.loader.exec_module(foo)
    return foo

#################################Determining if bash############################

py_kwds = {'import','from','def','lambda','class', 'try','except','raise','assert','finally',\
           'await','async','yield', 'if','or','not','elif','else','and','is', \
           'while','for','in','return','pass','break','continue', \
           'global','with','as','nonlocal',  'del',\
           'False','None','True'}

def numeric_str(x):
    try:
        _ = float(str(x))
        return True
    except:
        return False

def is_quoted(x):
    # Double quotes only, since they are bashy.
    if len(x)>=2:
        if x[0]=='"' and x[-1]=='"':
            return True
    return False

def bashy(token):
    # More likely to be bash than Python. Excludes ()[] unless in a quote.
    # Includes numbers.
    if len(token)>=2 and is_quoted(token):
        return True
    if ',' in token: # , is more Pythonic.
        return False
    if token in {'.','*','|','&'}:
        return True
    out = re.fullmatch('[-a-zA-Z0-9_]+', token)
    if out:
        return True
    return False

def is_pyvar(token):
    # Is this a python var we already set? Overriden by the "top 25" bashy commands.
    token = token.strip()

    if token in py_kwds:
        return True

    if token in pybashlib.top_25():
        return False
    py_vars = set(sys.modules[__name__].__dict__.keys())
    return token in py_vars

def split_by_eq(txt):
    # Splits a = b + c  => [a, [b,c]]. _ans if there is no eq.
    pieces = re.split('[ \t\n]+', txt)

    eq_ix = -1
    for i in range(len(pieces)):
        if pieces[i]=='=':
            eq_ix = i

    if eq_ix==-1:
        return ['_ans', pieces]
    else:
        return [' '.join(pieces[0:eq_ix]), pieces[eq_ix+1:]]

def attempt_shell_parse(txt):
    # Attempts a shell parse as a series of tokens.
    # Returns [python_var, f, args]

    txt = txt.strip()
    if '\n' in txt: # Does this restriction make sense?
        return None

    x = split_by_eq(txt)
    #print('Split x:', x)
    b4_eq = x[0]
    after_eq = x[1]
    all_bashy = len(list(filter(bashy, after_eq)))==len(after_eq)
    if not all_bashy: # Exit criterian 1: Non-bashy args.
        return None
    if is_pyvar(after_eq[0]):  # Exit criterian 2: Python var that is not in the top 25 bash vars.
        return None
    if len(after_eq)==1 and (numeric_str(after_eq[-1]) or is_quoted(after_eq[-1])): # Exit criterion 3: Single var set.
        return None
    return [b4_eq, after_eq[0], after_eq[1:]]

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
        lines = lines[mod_ix+1:]
    return (err+'\nTraceback:\n'+'\n'.join(lines)).strip()

class Shell:
    def __init__(self):

        self.cur_dir = '.' #TODO: default directory.
        self.outputs = [] # [message, is_error, input_ix]
        self.input_ix = 0
        self.listenerf = None

    def autocorrect(self, input):
        # TODO: simple shell commands with the path.
        x = attempt_shell_parse(input)
        if x is not None:
            return bashyparse2pystr(*x)
        return input

    def send(self, input, include_newline=True):
        self.cur_dir = os.path.realpath(self.cur_dir).replace('\\','/')
        input = input.strip()
        if len(input)>0:
            pybashlib.shell = self # So that fns from pybashlib works properly.
            vars0 = _module_vars()
            err = ''
            try:
                #https://stackoverflow.com/questions/23168282/setting-variables-with-exec-inside-a-function
                exec(input, globals(), globals())
                #print('Exed input:', input, 'dict:', sys.modules[__name__].__dict__.keys())
            except Exception as e:
                err = exc_to_str(e)

            vars1 = _module_vars()
            vars_set = ''
            for ky in vars1.keys():
                if vars1[ky] is not vars0.get(ky, None):
                    vars_set = vars_set+'\n'+ky+' = '+str1(vars1[ky])
            if len(vars_set)==0 and len(err)==0:
                vars_set = 'Command succeeded, no vars changed'

            if len(vars_set)>0:
                self.outputs.append([vars_set+'\n', False, self.input_ix])
            if len(err)>0:
                self.outputs.append([err+'\n', True, self.input_ix])

            self.listenerf() #Trigger it manually (since there is no IO stream).
            self.input_ix = self.input_ix+1

    def exit_shell(self):
        pass

    def add_update_listener(self, f, dt=0.0625):
        self.listenerf = f
