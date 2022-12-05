# Why the !@#$% to we have to write these!? Like, wouldn't going on to Chegg and getting a homework assignment for Python 101 be enough?
# os.chdir
import sys

shell = None # Modified this.

################################# Parsing tools ################################
# Example use of bash syntaxes:
#https://alvinalexander.com/linux-unix/recursive-grep-r-searching-egrep-find.



################################# Individual functions #########################

def grep(args):
    TODO

def ls(args):
    TODO

def cd(bashy_arg):
    TODO

################################################################################

def splat_here(modulename): # modulename = __name__ from within a module.
    var_dict = sys.modules[__name__].__dict__
    module = sys.modules[modulename]
    for k in var_dict.keys():
        if '__' not in k and k != 'shell':
            setattr(module, k, var_dict[k])

def top_25():
    # https://www.educative.io/blog/bash-shell-command-cheat-sheet
    out = {'ls', 'echo', 'touch', 'mkdir', 'grep', 'man', 'pwd', 'cd', 'mv',\
           'rmdir', 'locate', 'less', 'compgen', '>', 'cat', '|', 'head', \
            'tail', 'chmod', 'exit', 'history', 'clear', 'cp', 'kill', 'sleep'}
    return out
