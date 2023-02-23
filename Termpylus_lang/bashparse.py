# Simple bash-like parsing tools.
# Not intended to be a comprehensive bash parser or intrepreter.
import re
from . import pyparse
from Termpylus_shell import pybashlib, hotcmds1

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

def option_parse(args, paired_opts):
    # Returns {'flags': [-a, -b, -c, --foo, ...], 'pairs': {"-foo", "bar", ...}, 'tail': [a,b,c]}
    # Returns options, everything else.
    # Options are -foo or --bar.
    if type(args) is str:
        args = re.split(' +',args)
    paired_opts = set([p.replace('-','') for p in paired_opts])
    out = {'flags':[], 'pairs':{}, 'tail':[]}
    skip = False
    for i in range(len(args)):
        if skip:
            skip = False
            continue
        a = args[i]
        a = a.strip()
        a1 = a+'  '
        if a1[0]=='-' and (a in paired_opts or a.replace('-','') in paired_opts):
            out['pairs'][a] = args[i+1]
            skip = True
        elif a1[0:2]=='--':
            out['flags'].append(a)
        elif a1[0]=='-':
            add_fl = ['-'+c for c in a.replace('-','')]
            out['flags'] = out['flags']+add_fl # One or more single-char flags.
        else:
            out['tail'].append(a)
    return out

def is_pyvar(token, py_vars):
    # Is this a python var we already set? Overriden by the "top 25" bashy commands.
    token = token.strip()

    if token in pyparse.py_kwds:
        return True

    if token in pybashlib.top_bash() or token in set(hotcmds1.cmds1().keys()):
        return False

    return token in py_vars

def attempt_bash_parse(txt, pyvars):
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
    if is_pyvar(after_eq[0], pyvars):  # Exit criterian 2: Python var that is not in the top 25 bash vars.
        return None
    if len(after_eq)==1 and (numeric_str(after_eq[-1]) or is_quoted(after_eq[-1])): # Exit criterion 3: Single var set.
        return None
    return [b4_eq, after_eq[0], after_eq[1:]]

def bashyparse2pystr(out_var, cmd, args):
    # Equivalent python command.
    cmd_builtin = True # TODO: turn false when shell.
    cmds = pybashlib.top_bash().union(set(hotcmds1.cmds1().keys()))
    if cmd not in cmds:
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

def bash2py_autocorrect(txt_input, pyvars):
    # TODO: simple shell commands with the path.
    lines = txt_input.replace('\r\n','\n').split('\n')
    for i in range(len(lines)):
        x = attempt_bash_parse(lines[i], pyvars)
        if x is not None:
            lines[i] = bashyparse2pystr(*x)
    return '\n'.join(lines)
