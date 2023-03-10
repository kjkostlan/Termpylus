#Helpers for implementing bash functions. Not the funcions themselves (they are in bashy_cmds).
import sys, os, fnmatch, re, pathlib, operator
from tkinter import messagebox
from Termpylus_core import file_io

def option_parse(args, paired_opts):
    # Bash-like handling of arguments.
    # Returns {'flags': ["-a", "-b", "-c", "--foo", ...], 'pairs': {"-foo", "bar", ...}, 'tail': [a,b,c]}
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

def path_given_shell(fname, the_shell):
    # Absolute and relative paths behave differently.
    if file_io.is_path_absolute(fname):
        return file_io.absolute_path(fname)
    else:
        return file_io.absolute_path(the_shell.cur_dir+'/'+fname)

def bashy_file_info(fname):
    #https://flaviocopes.com/python-get-file-details/
    #https://www.geeksforgeeks.org/how-to-get-the-permission-mask-of-a-file-in-python/
    permiss = 'P'+oct(os.stat(fname).st_mode)[-3:]
    out = {'created':os.path.getctime(fname), 'modified':os.path.getmtime(fname),\
           'size':os.path.getsize(fname), 'permiss':permiss, 'name':fname,'ext':(fname+'.').split('.')[1]}
    return out

def filelist_wildcard(wildcard, is_recursive, include_folders=False):
    # Wildcard and regexp matching. wildcard should reperesent an absolute path.
    # is_recursive = False:
    #   If wildcard ends in a folder, all files inside will be choosen.
    #   If wildcard ends in a filename, the filename and any others that match will be choosen.

    wildcard = file_io.absolute_path(wildcard)

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
        path_pieces = wildcard.split('/')
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

    max_nonrecur_depth = len(wildcard.split('/'))
    pieces = wildcard.split('/')
    pieces1 = []
    for p in pieces:
        if '*' in p:
            break
        pieces1.append(p)
    return file_io.recursive_files('/'.join(pieces1), include_folders=include_folders, filter_fn=filter_fn, max_folder_depth=65536*is_recursive+max_nonrecur_depth)
