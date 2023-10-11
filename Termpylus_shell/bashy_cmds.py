# Commands designed for bash-like use (these get closured over the shell_obj for the actual command line).
# grep -i "the_string" the_file => x = grep("-i","the_string", the_file, shell_obj)
# Where shell_obj stores current directory, etc.
# Some of these are bash commands while others are extra commands for programming and debugging.
# os.chdir
# https://ss64.com/bash/
# Most of the vanilla bash commands don't seem to have libraries available thus the need to write them.
import sys, os, subprocess, operator
from Termpylus_core import projects
from . import bash_helpers

############################### Custom commands ################################

def rextern(bashy_args, shell_obj):
    print('Refreshing Termpylus_extern (this is mainly a debug tool during development of those packages)')
    import proj, code_in_a_box
    from Termpylus_extern.waterworks import py_updater
    proj._install_gitpacks(code_in_a_box)
    return py_updater.update_user_changed_modules()

def test1(bashy_args, shell_obj):
    if len(bashy_args)==0:
        return 'This test runs the code in Termpylus_test/scratchpad.py; such a file is intended for scratchwork. Similar use cases as startup.py.'
    from Termpylus_test import scratchpad # Delay import b/c it is importing many modules.
    return scratchpad.some_test(*bashy_args)

def dunwrap(bashy_args, shell_obj):
    if len(bashy_args)==0:
        return 'Unwraps a nested dictionary recursivly. see also to_dict.to_dict.'
    from Termpylus_core import dwalk
    return dwalk.unwrap(bashy_args[0])

def pflush(bashy_args, shell_obj):
    if len(bashy_args)==0:
        return 'Attempting to replace function references with updated versions (if there is any updated src code that is). Will not work on Tkinter callbacks.'
    from waterworks import py_updator
    return py_updater.function_flush()

def utest(bashy_args, shell_obj):
    # Unitests.
    print('**************Running unit tests**************')
    from Termpylus_test import test_pyrun, test_shell, test_walk, test_varmodtrack, test_pythonverse, test_parse, test_pyrun, ttools
    failures = {}
    for t_module in [test_shell, test_walk, test_varmodtrack, test_pythonverse, test_parse, test_pyrun]:
        if hasattr(t_module,'prepare_tests'):
            t_module.prepare_tests()
        failures = {**failures, **ttools.run_tests(t_module)}
        if hasattr(t_module,'postpare_tests'):
            t_module.postpare_tests()
    print('Failures; errors have debug info:')
    for k in failures.keys():
        print(k, failures[k])
    print('These failed:', list(failures.keys()))
    print('# failed:', len(failures))
    return len(failures)==0

def sfind(bashy_args, shell_obj=None):
    return projects.generic_source_find_with_bcast(bashy_args)

def pfind(bashy_args, shell_obj=None):
    from Termpylus_core import dquery
    if len(bashy_args)==0:
        return 'Search through the Pythonverse! Uses most of the options as sfind. Creating the pythonverse is slow, so use -ch to use the previous one.'
    return projects.generic_pythonverse_find_with_bcast(bashy_args)

def python(bashy_args, shell_obj, printouts=False):
    # Substantial modifications from the origina Python command.
    # Note: this function's printouts setting cannot be used if calling this by typing a line of bash code.
    from Termpylus_core import projects
    from Termpylus_extern.waterworks import paths
    if len(bashy_args)==0:
        return '''"python path/to/main.py" launches a Subprocess python project, prepending a modification onto main.py file to allow interaction.
                   "python origin dest_folder/main.py arg1 arg2 arg3" downloads/copies from the origin GitHub URL/folder, and sends args1-3 sys.argv. Dest_folder must be a local folder.
                   "python origin dest_folder main.py arg1 arg2 arg3" Alternative syntax.
                   "python -q ..." quits the project.
                   "python -b origin ..." specifies a GitHub branch; origin should be a GitHub URL in this case.
                   " python -which ..." finds a project and returns it.'''

    # Mutually exclusive first argument switches:
    arg0 = bashy_args[0].replace('--', '-').lower()
    if arg0 in ['-q','-quit']:
        # Exit out one or more projects.
        for qu in bashy_args[1:]:
            pr = projects.project_lookup(qu)
            if pr is None:
                raise Exception('Cannot find active project given query: '+qu)
            pr.quit()
        return
    if arg0 in ['-which','-who']:
        return projects.project_lookup(bashy_args[1])
    git_branch = None
    if arg0 in ['-branch', '-gitbranch', '-git-branch', '-git_branch']:
        git_branch = arg1
        bashy_args = bashy_args[2:]

    py_arg3 = len(bashy_args)>2 and bashy_args[2].endswith('.py')

    # The main purpose: launching a project.
    orig = bashy_args[0]
    dest = (bashy_args+[bashy_args[0]])[1]
    dest = bash_helpers.path_given_shell(dest, shell_obj)
    if not dest.endswith('.py'):
        raise Exception('The destination must specify the python file to be ran.')
    if py_arg3:
        dest_leaf = bashy_args[2]; dest_folder = dest
    else:
        dest_folder, dest_leaf = paths.folder_file(dest)

    if 'http' in orig.lower() or 'ftp' in orig.lower() or 'ssh' in orig.lower():
        pass
    else:
        orig = bash_helpers.path_given_shell(orig, shell_obj)
    if orig.endswith('.py'):
        orig, _ = paths.folder_file(orig)

    if (not py_arg3 and len(bashy_args)>2) or len(bashy_args)>3:
        cmd_args = bashy_args[(3 if py_arg3 else 2):]
    else:
        cmd_args = []
    out = projects.PyProj(orig, dest_folder, dest_leaf, mod_run_file='default', refresh_dt=3600, printouts=printouts, sleep_time=2, cmd_line_args=cmd_args, github_branch=git_branch)
    out.launch()
    return out

def pwatch(bashy_args, shell_obj=None):
    from Termpylus_extern.waterworks import var_watch
    #Not really needed: P = bash_helpers.option_parse(bashy_args, []); fl = set(P['flags']); kv = P['pairs']; x = P['tail']
    if len(bashy_args)==0:
        txt = '''
Adds or removes watchers to a given module. Watchers can be later queried using the -i and -o options of sfind.
Watchers are also added to all subprocesses.
"pwatch foo bar.baz" adds watchers to module foo and to "bar.baz" (which may be a module or a function within a module).
"pwatch --all": Adds ALL watchers. This may cause a significant performance hit and memory consumption.
"pwatch --rm foo bar" removes watchers from foo bar. It's possible to both add and remove watchers within one command.
'''
        return txt

    rm_mode = False
    for arg in bashy_args:
        if arg.replace('--','-') in ['-rm','-remove', '-delete', '-del']:
            rm_mode = True
            continue
        if arg.replace('--','-') in ['-a', '-all']:
            if rm_mode:
                projects.var_watch_remove_all_with_bcast()
            else:
                projects.var_watch_all_with_bcast()
        else:
            if rm_mode:
                projects.var_watch_remove_with_bcast(arg)
            else:
                projects.var_watch_add_with_bcast(arg)

def edits(bashy_args, shell_obj=None):
    if len(bashy_args)==0:
        return 'Returns a map from filename (if given -f) or modulename (if given -m) to edits.'
    bashy_args = [arg.replace('--','-') for arg in bashy_args]
    is_fname = '-f' in args or 'f' in args or '-file' in args or 'file' in args
    is_mname = '-m' in args or 'm' in args or '-module' in args or 'module' in args
    if is_fname and is_mname:
        raise Exception('Either a filename (-f) or modulename (-m) option must be choosen, but not both.')
    if not is_fname and not is_mname:
        raise Exception('Either a filename (-f) or modulename (-m) option must be choosen.')
    return projects.edits_with_bcast(is_fname)

############################### Vanilla commands ###############################

def grep(bashy_args, shell_obj):
    #grep [options] PATTERN [FILE...]
    #grep [options] [-e PATTERN | -f FILE] [FILE...]
    #Note: "grep foo ." will check all files in this folder for foo. This is slightly different behavior from is a directory.
    from . import RonenNess_grepfunc as grep_core
    from Termpylus_extern.waterworks import file_io
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
        txt = file_io.fload(fname)
        listy = grep_core.grep(txt, pattern, **kwargs)
        if len(listy)>0:
            out[fname] = listy

    return out

def ls(bashy_args, shell_obj):
    from Termpylus_extern.waterworks import file_io
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
    from Termpylus_extern.waterworks import file_io
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
    return bash_helpers.absolute_path('.', shell_obj)

def help(bashy_args, shell_obj):
    # This has been simplified considerably:
    kys = sys.modules[__name__].__dict__.keys()
    kys1 = list(filter(lambda x:'__' not in x, kys))
    return kys1

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

def sleep(bashy_args, shell_obj=None):
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
