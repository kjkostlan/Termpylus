# Commands designed for bash-like use (these get closured over the shell_obj for the actual command line).
# grep -i "the_string" the_file => x = grep("-i","the_string", the_file, shell_obj)
# Where shell_obj stores current directory, etc.
# Some of these are bash commands while others are extra commands for programming and debugging.
# os.chdir
# https://ss64.com/bash/
# Most of the vanilla bash commands don't seem to have libraries available thus the need to write them.
import sys, os, subprocess, operator
from . import bash_helpers

def help(bashy_args, shell_obj):
    # TODO: help is a dict and dict vals are more helpful.
    kys = sys.modules[__name__].__dict__.keys()
    kys1 = list(filter(lambda x:'__' not in x, kys))
    return kys1

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
        print('Attempting to replace function references with updated versions (if there is any updated src code that is). Will not work on Tkinter callbacks.')
    from Termpylus_py import mload
    return mload.function_flush()

def utest(bashy_args, shell_obj):
    # Unitests.
    print('**************Running unit tests**************')
    from Termpylus_test import test_pyrun, test_shell, test_walk, test_varmodtrack, test_pythonverse, test_parse, test_pyrun
    n_fail = 0
    for t_module in [test_pyrun, test_shell, test_walk, test_varmodtrack, test_pythonverse, test_parse, test_pyrun]:
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
    # Unlike "run" this does not spawn a seperate process: we want to access the processes internals after all.
    if len(bashy_args)==0:
        return 'Launch a Python project that you are working on. Can be a file or folder. Use -f to create a future in case of blocking main.py files.'

    # Runs a Python file much like a bash python command, except that it is ran in the current process.
    # What does this mean?
    # The file's folder is taken to be in the root of said python project (TODO: allow other options).
    # This root folder is prepended to sys.path, so that all imports within the project can work.
    # Our module names will almost certanly not conflict with the project.
    # However, multible projects may generate namespace collisions.
    #    I.e. if boh projects have a folder called 'extern'.
    #    (thus it is not recommended to work on multible projects, unless you decollide them).
    TODO #-f option makes a future.

    P = bash_helpers.option_parse(bashy_args, ['-m']); fl = set(P['flags']); kv = P['pairs']; x = P['tail'] # kv is empty
    if len(x)==0:
        raise Exception('Must specify filename to run.')
    pyfname = bash_helpers.absolute_path(x[0], shell_obj)
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

def pwatch(bashy_args, shell_obj):
    from Termpylus_core import var_watch
    return var_watch.bashy_set_watchers(*bashy_args)

def edits(bashy_args, shell_obj):
    from Termpylus_core import var_watch
    return var_watch.bashy_get_txt_edits(*bashy_args)

def grep(bashy_args, shell_obj):
    #grep [options] PATTERN [FILE...]
    #grep [options] [-e PATTERN | -f FILE] [FILE...]
    #Note: "grep foo ." will check all files in this folder for foo. This is slightly different behavior from is a directory.
    import Termpylus_extern.RonenNess_grepfunc as grep_core
    from Termpylus_core import file_io
    P = bash_helpers.option_parse(bashy_args, ['-e','-f']); fl = set(P['flags']); kv = P['pairs']; x = P['tail']
    pattern = kv.get('-e', x[-2])
    fname1 = bash_helpers.path_given_shell(x[-1], shell_obj)
    flist = bash_helpers.filelist_wildcard(fname1, '-r' in bashy_args, include_folders=False)

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
    from Termpylus_core import file_io
    P = bash_helpers.option_parse(bashy_args, []); fl = set(P['flags']); kv = P['pairs']; x = P['tail'] # kv is empty
    if len(x)==0:
        fname = '.'
    else:
        fname = x[0]

    # We flip -r and -R to be more consistent with most bash cmds.
    fname1 = bash_helpers.path_given_shell(fname, shell_obj)
    flist = bash_helpers.filelist_wildcard(fname1, '-r' in fl, include_folders=True)

    if '-a' in fl or '-A' in fl: # Include hidden files.
        pass
    else:
        flist = list(filter(lambda x: not file_io.is_hidden(x), flist))

    flist = [bash_helpers.bashy_file_info(fnm) for fnm in flist]

    sort_ky = 'name'
    if '-S' in bashy_args:
        sort_ky = 'size'
    elif '-t' in bashy_args:
        sort_ky = 'name'
    elif '-X' in bashy_args:
        sort_ky = 'ext'
    flist = list(sorted(flist, key=operator.itemgetter(sort_ky)))

    if '-R' in bashy_args: # We flip -r and -R to be more consistent with most bash cmds.
        flist.reverse()

    sep = ' '
    if '-l' in bashy_args:
        sep = '\n'

    # How to show files:
    def showfile(fl):
        fname = fl['name']
        if '-r' not in bashy_args:
            fname = fname.split('/')[-1]
        if '-l' in bashy_args: # full list (a bit simplier than bashe's arcane options)
            return fl['permiss']+' '+str(fl['size'])+' '+str(fl['modified'])+' '+fname
        elif '-s' in bashy_args:
            return str(fl['size'])+' '+fname
        else:
            return fname

    return sep.join([showfile(f) for f in flist])

def cd(bashy_args, shell_obj):
    from Termpylus_core import file_io
    fname = bashy_args[0]
    fname1 = bash_helpers.path_given_shell(fname, shell_obj)
    flist = bash_helpers.filelist_wildcard(fname1, False, include_folders=True)

    if len(flist)==0:
        raise Exception('No such file or directory:'+str(fname))
    else:
        if not os.path.isdir(flist[0]):
            flist[0] = '/'.join(flist[0].split('/')[0:-1]) # It tends to be one level too deep.
        shell_obj.cur_dir = flist[0]
        return shell_obj.cur_dir

def rm(bashy_args, shell_obj):
    # DANGER DANGER DANGER. You have been warned.
    P = bash_helpers.option_parse(bashy_args, []); fl = set(P['flags']); kv = P['pairs']; x = P['tail'] # kv is empty
    fname = x[0]

    if fname=='/' and '--no-preserve-root' not in fl:
        raise Exception('rm called on root dir. If you really need that, add --no-preserve-root.')

    if '-r' in fl and '-f' not in fl and debug_folder_restrictions is None:
        answer = messagebox.askokcancel("Rm is dangerous!","Rm cant be undone. Are your sure you want to run it with -r?")
        if not answer:
            raise Exception('rm cmd averted by user.')

    fname1 = bash_helpers.path_given_shell(fname, shell_obj)
    outer_flist = bash_helpers.filelist_wildcard(fname1, False, include_folders='-r' in fl)
    inner_flist = bash_helpers.filelist_wildcard(fname1, '-r' in fl, include_folders='-r' in fl)

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

def run(bashy_args, shell_obj):
    # Single-shot run, returns result and sets last_run_err
    # https://stackoverflow.com/questions/89228/how-do-i-execute-a-program-or-call-a-system-command
    dir = bash_helpers.absolute_path('.', shell_obj)
    #https://stackoverflow.com/questions/17742789/running-multiple-bash-commands-with-subprocess
    cmd = 'cd '+dir+'\n'+' '.join(bashy_args)
    #result = subprocess.run([cmd]+cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    x = '/bin/bash'
    if os.name == 'nt':
        x = 'cmd'
    process = subprocess.Popen(x, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = process.communicate(cmd)

    out = result.stdout.decode('utf-8')
    err = result.sdterr.decode('utf-8')
    shell_obj.err = err
    return out
