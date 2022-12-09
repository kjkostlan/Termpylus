# Why the !@#$% to we have to write these!? Like, wouldn't going on to Chegg and getting a homework assignment for Python 101 be enough?
# os.chdir
# https://ss64.com/bash/
import sys, os
import extern.RonenNess_grepfunc as grep_core
shell = None # This has the current directory in it.
debug_folder_restrictions = None # Restrict all changes to this folder b/c in case files are deleted.

############################### Directory stuff ################################

def absolute_path(fname):
    # Loads a file given an absolute path.
    fname = fname.replace('\\','/')
    if fname[0]=='/': # How bash defines absolute paths.
        return fname
    else:
        return os.path.abspath((shell.cur_dir+'./'+fname)).replace('\\','/')

def is_hidden(fname):
    # Is the filename hidden.
    return absolute_path(fname).split('/')[-1][0] == '.'

def file_info(fname):
    fname = absolute_path(fname)
    #https://flaviocopes.com/python-get-file-details/
    #https://www.geeksforgeeks.org/how-to-get-the-permission-mask-of-a-file-in-python/
    parmiss = 'P'+oct(os.stat(filename).st_mode)[-3:]
    out = {'created':os.path.getctime(fname), 'modified':os.path.getmtime(fname),\
           'size':os.path.getsize(fname), 'permiss':parmiss, 'name':fname,'ext':(fname+'.').split('.')[1]}
    return out

def file_load(fname, linux_newlines=True):
    fname = absolute_path(fname)
    # Loads a file relative to the shell.
    with open(fname,'r') as f:
        out = fname.read()
        if linux_newlines:
            out = out.replace()
    return out

def files_in_folder1(fname):
    fname = absolute_path(fname)
    files = os.listdir(fname)
    return [fname+'/'+file for file in files]

def wildcard_matches(listy, matcher):
    out = []
    for l in listy:
        if matcher==l:
            out.append(l)
        elif fnmatch.fnmatch(l, matcher): #https://stackoverflow.com/questions/34660530/find-strings-in-list-using-wildcard
            out.append(l)
        else: # We allow regexps (most would have to be quoted to trigger bash2python).
            try:
                if re.fullmatch(matcher, l) is not None:
                    out.append(l)
            except re.error:
                pass
    return out

def recursive_files_core(fname, include_folders=False):
    fname = absolute_path(fname)
    if os.isdir(fname):
        files1 = files_in_folder1(fname)
        out = []
        for f in files1:
            if os.isdir(f):
                if include_folders:
                    out.append(f)
                out = out+recursive_files_core(f, include_folders)
        return out
    else:
        return [fname]

def filelist_wildcard(wildcard, is_recursive, include_folders=False):
    files_leaf = os.listdir(shell.cur_dir)
    matches = wildcard_matches(files_leaf)
    matches_full = [absolute_path(m) for m in matches]
    if is_recursive:
        out = []
        for m in matches_full:
            out = out+recursive_files_core(m, include_folders)
    else:
        return matches_full
    files1 = files_in_folder1(fname)

#shell.cur_dir

################################# Parsing tools ################################
# Example use of bash syntaxes:
#https://alvinalexander.com/linux-unix/recursive-grep-r-searching-egrep-find.

def option_parse(args, paired_opts):
    # Returns {'flags': [-a, -b, -c, ...], 'pairs': {"-foo", "bar", ...}, 'tail': [a,b,c]}
    # Returns options, everything else.
    # Options are -foo or --bar.
    paired_opts = set([p.replace('-','') for p in paired_opts])
    out = {'flags':[], 'pairs':[], 'tail':[]}
    skip = False
    for i in range(len(args)):
        if skip:
            continue
        a = args[i]
        a = a.strip()
        if a.replace('-','') in paired_opts:
            pairs[a] = args[i+1]
            skip = True
        elif '--' in a:
            out['flags'].append(a)
        elif '-' in a:
            out['flags'] = out['flags']+list(a.replace('-','')) # One or more single-char flags.
        else:
            tail.append(a)
    return out

################################# Individual functions #########################

def grep(args):
    #grep [options] PATTERN [FILE...]
    #grep [options] [-e PATTERN | -f FILE] [FILE...]
    P = option_parse(args, ['-e','-f']); fl = set(P['flags']); kv = P['pairs']; x = P['tail']
    pattern = kv_pairs.get('-e', x[-2])
    flist = filelist_wildcard(x[-1], '-r' in args, include_folders=False)

    fl = fl-set(['-r']) # they have a -r flag that is non-standard, but we use it for recursive.
    for k in kv.keys():
        fl.add(k)

    out = {}
    for fname in files:
        txt = file_load(fname)
        out[fname] = grep_core.grep(txt, pattern, list(fl))

    return out

def ls(args):
    P = option_parse(args, []); fl = set(P['flags']); kv = P['pairs']; x = P['tail'] # kv is empty
    fname = x[0]

    # We flip -r and -R to be more consistent with most bash cmds.
    flist = filelist_wildcard(fname, '-r' in args, include_folders=False)

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
    flist = list(sorted(flist, key=itemgetter(sort_ky)))

    if '-R' in args: # We flip -r and -R to be more consistent with most bash cmds.
        flist.reverse()

    sep = ' '
    if '-l' in args:
        sep = '\n'

    # How to show files:
    def showfile(fl):
        if '-l' in args: # full list (a bit simplier than bashe's arcane options)
            return fl['permiss']+' '+fl['size']+' '+fl['modified']+' '+fl['name']
        elif '-s' in args:
            return fl['size']+' '+fl['name']
        else:
            return fl['name']

    return sep.join([showfile(fl) for fl in flist])

def cd(args):
    fname = absolute_path(args[-1])
    flist = filelist_wildcard(fname, False, include_folders=True)
    if len(flist)==0:
        raise Exception('No such file or directory:'+str(fname))
    else:
        shell.cur_dir = flist[0]
        return flist[0]

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
