# Why the !@#$% to we have to write these!? Like, wouldn't going on to Chegg and getting a homework assignment for Python 101 be enough?
# os.chdir
# https://ss64.com/bash/
import sys, os, fnmatch, re, pathlib, operator
from tkinter import messagebox
import Termpylus_extern.RonenNess_grepfunc as grep_core
from Termpylus_py import mload

shell = None # This has the current directory in it.
debug_only_these_folders = None # Restrict all file writes and deletes to this folder b/c in case files are deleted. Use GLOBAL paths here.

############################### Directory stuff ################################

def absolute_path(fname, the_shell=None):
    # Loads a file given an absolute path.
    fname = fname.replace('\\','/')
    linux_abspath = fname[0]=='/'
    win_abspath = len(fname)>2 and fname[1]==':' # C:/path/to/directore
    if the_shell is None:
        the_shell = shell
    if linux_abspath or win_abspath: # Two ways of getting absolute paths.
        return fname
    else:
        cur_dir = os.path.abspath(shell.cur_dir).replace('\\','/')
        out = os.path.abspath(cur_dir+'./'+fname).replace('\\','/')
        return out

def is_hidden(fname):
    # Is the filename hidden.
    return absolute_path(fname).split('/')[-1][0] == '.'

def file_info(fname):
    fname = absolute_path(fname)
    #https://flaviocopes.com/python-get-file-details/
    #https://www.geeksforgeeks.org/how-to-get-the-permission-mask-of-a-file-in-python/
    parmiss = 'P'+oct(os.stat(fname).st_mode)[-3:]
    out = {'created':os.path.getctime(fname), 'modified':os.path.getmtime(fname),\
           'size':os.path.getsize(fname), 'permiss':parmiss, 'name':fname,'ext':(fname+'.').split('.')[1]}
    return out

def file_load(fname, linux_newlines=True):
    fname = absolute_path(fname)
    # Loads a file relative to the shell.
    with open(fname,'r') as f:
        out = f.read()
        if linux_newlines:
            out = out.replace('\r\n','\n')
    return out

def files_in_folder1(fname):
    # Fullpath.
    fname = absolute_path(fname)
    files = os.listdir(fname)
    return [(fname+'/'+file).replace('//','/') for file in files]

def recursive_files_core(fname, include_folders=False, filter_fn=None, max_folder_depth=65536):
    fname = absolute_path(fname)
    if os.path.isdir(fname):
        files1 = files_in_folder1(fname)
        out = []
        for f in files1:
            if filter_fn is not None and not filter_fn(f):
                continue
            if os.path.isdir(f):
                if include_folders:
                    out.append(f)
                if len(fname.split('/'))<max_folder_depth:
                    out = out+recursive_files_core(f, include_folders, filter_fn, max_folder_depth)
            else:
                out.append(f)
        return out
    else:
        if filter_fn(fname):
            return [fname]
        else:
            return []

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
    return recursive_files_core('/'.join(pieces1), include_folders=include_folders, filter_fn=filter_fn, max_folder_depth=65536*is_recursive+max_nonrecur_depth)

def _fileallow(fname):
    keeplist = debug_only_these_folders
    fname = absolute_path(fname)
    if keeplist is not None:
        if type(keeplist) is str:
            keeplist = [keeplist]
        keeplist = [os.path.realpath(kl).replace('\\','/') for kl in keeplist]
        allow = False
        for k in keeplist:
            if fname.startswith(k):
                allow = True
        return allow
    else:
        return True

def gaurded_delete(fname, allow_folders=False):
    # Deleting is dangerous.
    fname = absolute_path(fname)
    if not _fileallow(fname):
        raise Exception('debug_only_these_folders is set to: '+str(debug_only_these_folders).replace('\\\\','/')+' and disallows deleting this filename: '+fname)
    if os.path.isdir(fname) and not allow_folders:
        raise Exception('Attempt to delete folder (and whats inside) when allow_folders=False.')

def guarded_create(fname, is_folder):
    # Creating files isn't all that dangerous, but still can be annoying.
    # Skips files that already exist.
    fname = absolute_path(fname)
    if not _fileallow(fname):
        raise Exception('debug_only_these_folders is set to: '+str(debug_only_these_folders).replace('\\\\','/')+' and disallows creating this filename: '+fname)
    if is_folder:
        folder = fname
    else:
        folder, _ = os.path.split(fname)
    #https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
    if not is_folder:
        with open(fname,'a') as _:
            pass
    return fname

################################# Parsing tools ################################
# Example use of bash syntaxes:
#https://alvinalexander.com/linux-unix/recursive-grep-r-searching-egrep-find.

def option_parse(args, paired_opts):
    # Returns {'flags': [-a, -b, -c, --foo, ...], 'pairs': {"-foo", "bar", ...}, 'tail': [a,b,c]}
    # Returns options, everything else.
    # Options are -foo or --bar.
    if type(args) is str:
        args = [args]
    paired_opts = set([p.replace('-','') for p in paired_opts])
    out = {'flags':[], 'pairs':{}, 'tail':[]}
    skip = False
    for i in range(len(args)):
        if skip:
            continue
        a = args[i]
        a = a.strip()
        a1 = a+'  '
        if a1[0]=='-' and a.replace('-','') in paired_opts:
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

################################# Individual functions #########################

def grep(args):
    #grep [options] PATTERN [FILE...]
    #grep [options] [-e PATTERN | -f FILE] [FILE...]
    #Note: "grep foo ." will check all files in this folder for foo. This is slightly different behavior from is a directory.
    P = option_parse(args, ['-e','-f']); fl = set(P['flags']); kv = P['pairs']; x = P['tail']
    pattern = kv.get('-e', x[-2])
    flist = filelist_wildcard(x[-1], '-r' in args, include_folders=False)

    fl = fl-set(['-r']) # they have a -r flag that is non-standard, but we use it for recursive.
    kwargs = {}
    for k in kv.keys():
        kwargs[k.replace('-','')] = kv[k]
    for f in fl:
        kwargs[f.replace('-','')] = True

    out = {}
    for fname in flist:
        txt = file_load(fname)
        listy = grep_core.grep(txt, pattern, **kwargs)
        if len(listy)>0:
            out[fname] = listy

    return out

def ls(args):
    P = option_parse(args, []); fl = set(P['flags']); kv = P['pairs']; x = P['tail'] # kv is empty
    if len(x)==0:
        fname = '.'
    else:
        fname = x[0]

    # We flip -r and -R to be more consistent with most bash cmds.
    flist = filelist_wildcard(fname, '-r' in fl, include_folders=True)

    if '-a' in fl or '-A' in fl: # Include hidden files.
        pass
    else:
        flist = list(filter(lambda x: not is_hidden(x), flist))

    flist = [file_info(fnm) for fnm in flist]

    sort_ky = 'name'
    if '-S' in args:
        sort_ky = 'size'
    elif '-t' in args:
        sort_ky = 'name'
    elif '-X' in args:
        sort_ky = 'ext'
    flist = list(sorted(flist, key=operator.itemgetter(sort_ky)))

    if '-R' in args: # We flip -r and -R to be more consistent with most bash cmds.
        flist.reverse()

    sep = ' '
    if '-l' in args:
        sep = '\n'

    # How to show files:
    def showfile(fl):
        fname = fl['name']
        if '-r' not in args:
            fname = fname.split('/')[-1]
        if '-l' in args: # full list (a bit simplier than bashe's arcane options)
            return fl['permiss']+' '+str(fl['size'])+' '+str(fl['modified'])+' '+fname
        elif '-s' in args:
            return str(fl['size'])+' '+fname
        else:
            return fname

    return sep.join([showfile(f) for f in flist])

def cd(args):
    fname = absolute_path(args[-1])
    flist = filelist_wildcard(fname, False, include_folders=True)
    if len(flist)==0:
        raise Exception('No such file or directory:'+str(fname))
    else:
        if not os.path.isdir(flist[0]):
            flist[0] = '/'.join(flist[0].split('/')[0:-1]) # It tends to be one level too deep.
        shell.cur_dir = flist[0]
        return shell.cur_dir

def rm(args):
    # DANGER DANGER DANGER. You have been warned.
    P = option_parse(args, []); fl = set(P['flags']); kv = P['pairs']; x = P['tail'] # kv is empty
    fname = x[0]

    if fname=='/' and '--no-preserve-root' not in fl:
        raise Exception('rm called on root dir. If you really need that, add --no-preserve-root.')

    if '-r' in fl and '-f' not in fl and debug_folder_restrictions is None:
        answer = messagebox.askokcancel("Rm is dangerous!","Rm cant be undone. Are your sure you want to run it with -r?")
        if not answer:
            raise Exception('rm cmd averted by user.')

    outer_flist = filelist_wildcard(fname, False, include_folders='-r' in fl)
    inner_flist = filelist_wildcard(fname, '-r' in fl, include_folders='-r' in fl)

    for f in outer_flist:
        gaurded_delete(f, '-r' in fl)

    return inner_flist

def pwd(args):
    return absolute_path('.')

def touch(args):
    TODO

def mkdir(args):
    TODO

def utest(args):
    # Unitests.
    print('**Running unit tests**')
    from Termpylus_test import test_pyrun # Better to not have circular dependencies.
    if not test_pyrun.run_tests():
        return False
    from Termpylus_test import test_shell
    if not test_shell.run_tests():
        return False
    return True

def utest0(args):
    # Scratchwork tests go here. Reset to 'return True' when git commiting.
    import Termpylus_test.test_pyrun
    Termpylus_test.test_pyrun.test_py_import0()
    return mload.module_file('smain')


################################################################################

def splat_here(modulename): # modulename = __name__ from within a module.
    var_dict = sys.modules[__name__].__dict__
    module = sys.modules[modulename]
    for k in var_dict.keys():
        if '__' not in k and k != 'shell':
            setattr(module, k, var_dict[k])

def top_25():
    # Top 25 with a couple of changes.
    # https://www.educative.io/blog/bash-shell-command-cheat-sheet
    out = {'ls', 'echo', 'touch', 'mkdir', 'grep', 'man', 'pwd', 'cd', 'mv',\
           'rm', 'locate', 'less', 'compgen', '>', 'cat', '|', 'head', \
            'tail', 'chmod', 'exit', 'history', 'clear', 'cp', 'kill', 'sleep'}
    out.add('utest'); out.add('utest0') # Not a bash command but allows us to run unit tests.
    return out
