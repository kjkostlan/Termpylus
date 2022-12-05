# Python shell with some wrappers for simple linux commands.
# It holds a current working directory to feel shell-like.
import sys, re
import pybashlib
import traceback

def str1(x):
    sx = str(x)
    if len(sx)>512:
        sx = '<big thing>'
    return sx

def _module_strs():
    modl = sys.modules[__name__]
    return dict(zip(modl.__dict__.keys(), [str(x) for x in modl.__dict__.values()]))

py_kwds = {'import','from','def','lambda','class', 'try','except','raise','assert','finally',\
           'await','async','yield', 'if','or','not','elif','else','and','is', \
           'while','for','in','return','pass','break','continue', \
           'global','with','as','nonlocal',  'del',\
           'False','None','True'}

pybashlib.splat_here(__name__)

def run(cmd, sys_args):
    # Single-shot run, return result.
    TODO

def tail_arg_deep_assess(tail):
    # Is this bashy or a Python arg?
    tail = tail.strip()

    if tail in pybashlib.top_25():
        return True
    py_vars = set(sys.modules[__name__].__dict__.keys())
    return tail not in py_vars

def attempt_shell_parse(txt):
    # Attempts a shell parse as a series of tokens.
    # Returns [python_var, f, args]

    def bashy(token):
        # More likely to be bash than Python.
        if len(token)>=2:
            if token[0]=='"' and token[-1]=='"':
                return True
        if token in {'.','*','|','&'}:
            return True
        return re.fullmatch('[-a-zA-Z0-9_]+', token)

    txt = txt.strip()
    if '\n' in txt: # Does this restriction make sense?
        return None

    var_name = None
    pieces = re.split('[ \t\n]+', txt)

    if len(pieces) < 2:
        return None

    if pieces[0] in py_kwds:
        return None # Python code.

    # Equal index.
    eq_ix = -1
    for i in range(len(pieces)):
        if pieces[i]=='=':
            eq_ix = i

    after_eq = pieces[eq_ix:]
    all_bashy = len(list(filter(bashy, after_eq)))==len(after_eq)
    if not all_bashy: # too much of a hair trigger?
        return None

    if len(pieces) < eq_ix+2: # too stubby!
        return None

    if len(pieces) == eq_ix+2 and eq_ix>0: # a = b format, but is b from Python?
        if not tail_arg_deep_assess(pieces[-1]):
            return None

    if eq_ix==-1:
        return [None, pieces[0], pieces[1:]]
    else:
        return [' '.join(pieces[0:eq_ix]), pieces[eq_ix+1], pieces[eq_ix+2:]]

def bashyparse2pystr(out_var, cmd, args):
    # Equivalent python command.
    cmd_builtin = True # TODO: turn false when shell.
    if out_var is None:
        out_var = 'ans' # Default.
    def quote_if_needed(x):
        if '"' in x or "'" in x:
            return x
        return '"'+x+'"'

    arg_str = '['+','.join([quote_if_needed(a) for a in args])+']'
    if not cmd_builtin:
        return '%s = run(%s, %s)'%(str(out_var), str(cmd), arg_str)
    else:
        return '%s = %s(%s)'%(str(out_var), str(cmd), arg_str)

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
        input = input.strip()
        if len(input)>0:
            pybashlib.shell = self # So that fns from pybashlib works properly.
            strs0 = _module_strs()
            err = ''
            try:
                #https://stackoverflow.com/questions/23168282/setting-variables-with-exec-inside-a-function
                exec(input, globals(), globals())
                #print('Exed input:', input, 'dict:', sys.modules[__name__].__dict__.keys())
            except Exception as e:
                err = exc_to_str(e)

            strs1 = _module_strs()
            vars_set = ''
            for ky in strs1.keys():
                if strs1[ky] != strs0.get(ky, None):
                    vars_set = vars_set+'\n'+ky+' = '+str1(eval(ky))
            if len(vars_set)==0 and len(err)==0:
                vars_set = 'Command succeeded'

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
