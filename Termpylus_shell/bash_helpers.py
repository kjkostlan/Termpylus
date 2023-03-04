#Helpers for implementing bash functions. Not the funcions themselves (they are in bashy_cmds).
import sys, os, fnmatch, re, pathlib, operator
from tkinter import messagebox

def option_parse(args, paired_opts):
    # Bash-like handling of arguments.
    # Returns {'flags': [-a, -b, -c, --foo, ...], 'pairs': {"-foo", "bar", ...}, 'tail': [a,b,c]}
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

############################### Directory stuff ################################

def absolute_path(fname, the_shell):
    # Linux-a-fies the file name.
    fname = fname.replace('\\','/')
    linux_abspath = fname[0]=='/'
    win_abspath = len(fname)>2 and fname[1]==':' # C:/path/to/folder
    if linux_abspath or win_abspath: # Two ways of getting absolute paths.
        return fname
    else:
        cur_dir = os.path.abspath(the_shell.cur_dir).replace('\\','/')
        out = os.path.abspath(cur_dir+'./'+fname).replace('\\','/')
        return out

def is_hidden(fname):
    # Is the filename hidden.
    return absolute_path(fname).split('/')[-1][0] == '.'

def bashy_file_info(fname):
    #https://flaviocopes.com/python-get-file-details/
    #https://www.geeksforgeeks.org/how-to-get-the-permission-mask-of-a-file-in-python/
    permiss = 'P'+oct(os.stat(fname).st_mode)[-3:]
    out = {'created':os.path.getctime(fname), 'modified':os.path.getmtime(fname),\
           'size':os.path.getsize(fname), 'permiss':permiss, 'name':fname,'ext':(fname+'.').split('.')[1]}
    return out

def filelist_wildcard(wildcard, is_recursive, include_folders=False):
    # Wildcard and regexp matching.
    # is_recursive = False:
    #   If wildcard ends in a folder, all files inside will be choosen.
    #   If wildcard ends in a filename, the filename and any others that match will be choosen.
    path_global = absolute_path(wildcard)

    def leaf_star(leafname, leaf_wild):
        # Includes regexps, but they can't have forward slashes.
        if leafname==leaf_wild:
            return True
        if fnmatch.fnmatch(leafname, leaf_wild):
            return True
        try:
            if re.fullmatch(leaf_wild, leafname) is not None:
                return True
        except re.error:
            return False
        return False

    def filter_fn(fname_global):
        pieces = fname_global.split('/') #regexs allowed if they dont have *forward* slash.
        path_pieces = path_global.split('/')
        n_piece = len(pieces)
        n_glob = len(path_pieces)
        if n_piece>n_glob: # Digging deeper.
            return True
        elif leaf_star(pieces[n_piece-1], path_pieces[n_piece-1]):
            return True
        else:
            #print('Leaf star test:', pieces[n_piece-1], path_pieces[n_piece-1], leaf_star(pieces[n_piece-1], path_pieces[n_piece-1]))
            return False
        return False

    max_nonrecur_depth = len(path_global.split('/'))
    pieces = path_global.split('/')
    pieces1 = []
    for p in pieces:
        if '*' in p:
            break
        pieces1.append(p)
    return file_io.recursive_files('/'.join(pieces1), include_folders=include_folders, filter_fn=filter_fn, max_folder_depth=65536*is_recursive+max_nonrecur_depth)

#def top_bash():
#    # Top 25 with a couple of changes.
#    # https://www.educative.io/blog/bash-shell-command-cheat-sheet
#    out = {'ls', 'echo', 'touch', 'mkdir', 'grep', 'man', 'pwd', 'cd', 'mv',\
#           'rm', 'locate', 'less', 'compgen', '>', 'cat', '|', 'head', \
#            'tail', 'chmod', 'exit', 'history', 'clear', 'cp', 'kill', 'sleep'}
#    return out
