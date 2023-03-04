# Commands designed for bash-like use (these get closured over the shell_obj for the actual command line).
# grep -i "the_string" the_file => x = grep("-i","the_string", the_file, shell_obj)
# Where shell_obj stores current directory, etc.
# Some of these are bash commands while others are extra commands for programming and debugging.
# os.chdir
# https://ss64.com/bash/
# Most of the vanilla bash commands don't seem to have libraries available thus the need to write them.
import sys
from Termpylus_core import var_watch, dquery
from . import bash_helpers

debug_restrict_disk_modifications_to_these = None # Restrict all file writes and deletes to this folder b/c in case files are deleted. Use GLOBAL paths here.

def help(bashy_args, shell_obj):
    # TODO: help is a dict and dict vals are more helpful.
    kys = sys.modules[__name__].__dict__.keys()
    kys1 = list(filter(lambda x:'__' not in x, kys))
    return list(out.keys())

def test1(bashy_args, shell_obj):
    if len(bashy_args)==0:
        print('This test is running the test.scratchpad function. Best used when debugging a single unit test.')
    from Termpylus_test import scratchpad # Delay import b/c it is importing many modules.
    return scratchpad.some_test(*bashy_args)

def dunwrap(bashy_args, shell_obj):
    if len(bashy_args)==0:
        return 'Unwraps a nested dictionary recursivly. see also to_dict.to_dict.'
    from Termpylus_py import walk
    return walk.unwrap(bashy_args[0])

def pflush(bashy_args, shell_obj):
    if len(bashy_args)==0:
        print('Attempting to flush function references with updated versions. Will not work on Tkinter callbacks.')
    from Termpylus_py import mload
    return mload.function_flush()

def utest(ashy_args, shell_obj):
    # Unitests.
    print('**************Running unit tests**************')
    from Termpylus_test import test_pyrun, test_shell, test_walk, test_varmodtrack, test_pythonverse, test_parse
    n_fail = 0
    for t_module in [test_pyrun, test_shell, test_walk, test_varmodtrack, test_pythonverse, test_parse]:
        if not t_module.run_tests():
            print('>>testing failed for:', t_module)
            n_fail = n_fail+1
    print('!!>>!!>>Number of failed modules:', n_fail)
    return n_fail==0

def sfind(bashy_args, shell_obj):
    from Termpylus_core import dquery
    return dquery.source_find(*bashy_args)

def pfind(bashy_args, shell_obj):
    from Termpylus_core import dquery
    if len(bashy_args)==0:
        return 'Search through the Pythonverse! Uses most of the options as sfind. Creating the pythonverse is slow, so use -ch to use the previous one.'
    pythonverse = TODO
    TODO # -ch for cache.
    return dquery.generic_find(bashy_args, pythonverse)

def python(bashy_args, shell_obj):
    if len(bashy_args)==0:
        return 'Launch a Python project that you are working on. Can be a file or folder. Use -f to create a future in case of blocking main.py files.'
    TODO #-f option makes a future.

def pwatch(bashy_args, shell_obj):
    return var_watch.bashy_set_watchers(*bashy_args)

def edits(bashy_args, shell_obj):
    return var_watch.bashy_get_txt_edits(*bashy_args)

def grep(bashy_args, shell_obj):
    #grep [options] PATTERN [FILE...]
    #grep [options] [-e PATTERN | -f FILE] [FILE...]
    #Note: "grep foo ." will check all files in this folder for foo. This is slightly different behavior from is a directory.
    import Termpylus_extern.RonenNess_grepfunc as grep_core
    P = bashparse.option_parse(args, ['-e','-f']); fl = set(P['flags']); kv = P['pairs']; x = P['tail']
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
        txt = file_io.contents(fname)
        listy = grep_core.grep(txt, pattern, **kwargs)
        if len(listy)>0:
            out[fname] = listy

    return out

def ls(bashy_args, shell_obj):
    P = bashparse.option_parse(args, []); fl = set(P['flags']); kv = P['pairs']; x = P['tail'] # kv is empty
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

    flist = [bashy_file_info(fnm) for fnm in flist]

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

def cd(bashy_args, shell_obj):
    fname = absolute_path(args[-1])
    flist = filelist_wildcard(fname, False, include_folders=True)
    if len(flist)==0:
        raise Exception('No such file or directory:'+str(fname))
    else:
        if not os.path.isdir(flist[0]):
            flist[0] = '/'.join(flist[0].split('/')[0:-1]) # It tends to be one level too deep.
        shell.cur_dir = flist[0]
        return shell.cur_dir

def rm(bashy_args, shell_obj):
    # DANGER DANGER DANGER. You have been warned.
    P = bashparse.option_parse(args, []); fl = set(P['flags']); kv = P['pairs']; x = P['tail'] # kv is empty
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

def pwd(bashy_args, shell_obj):
    return absolute_path('.')

def touch(bashy_args, shell_obj):
    TODO

def mkdir(bashy_args, shell_obj):
    TODO

def HOME(bashy_args, shell_obj):
    # The ~ or $HOME directory.
    TODO

def echo(bashy_args, shell_obj):
    return ' '.join([str(x) for x in bashy_args])

def man(bashy_args, shell_obj):
    TODO

def mv(bashy_args, shell_obj):
    TODO

def locate(bashy_args, shell_obj):
    TODO

def less(bashy_args, shell_obj):
    TODO

def compgen(bashy_args, shell_obj):
    TODO

def cat(bashy_args, shell_obj):
    TODO

def head(bashy_args, shell_obj):
    TODO

def tail(bashy_args, shell_obj):
    TODO

def chmod(bashy_args, shell_obj):
    TODO

def exit(bashy_args, shell_obj):
    TODO

def history(bashy_args, shell_obj):
    TODO

def clear(bashy_args, shell_obj):
    TODO

def cp(bashy_args, shell_obj):
    TODO

def kill(bashy_args, shell_obj):
    TODO

def sleep(bashy_args, shell_obj):
    TODO
