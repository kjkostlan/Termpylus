# Handles projects.
import sys, os, time, shutil, re
import code_in_a_box, proj
from Termpylus_shell import bashy_cmds, shellpython
from Termpylus_extern.waterworks import file_io, eye_term

_gl = proj.global_get('Termpylus_proj_globlas', {'active_projs':[], 'dead_projs':[] , 'num_cmds_total'=0})

def cwalk(f, x, leaf_only=True):
    # Simple collection walk. Used in the subprocess to wrap objects as strings.
    ty = type(x)
    if type(x) is dict:
        x = x if leaf_only else f(x)
        return dict(zip([cwalk(f, k, leaf_only) for k in x.keys()], [cwalk(f, v, leaf_only) for v in x.values()]))
    elif type(x) is list:
        x = x if leaf_only else f(x)
        return [cwalk(f, xi, leaf_only) for xi in x]
    elif type(x) is set:
        x = x if leaf_only else f(x)
        return set([cwalk(f, xi, leaf_only) for xi in x])
    elif type(x) is tuple:
        x = x if leaf_only else f(x)
        return tuple([cwalk(f, xi, leaf_only) for xi in x])
    else:
        return f(x)

def get_prepend(sleep_time=2):
    # Before the main code runs we need to set up.
    local_ph = os.path.realpath('.').replace('\\','/')
    txt = '''
import os, sys, traceback, threading

if "LOCALPH" not in sys.path: # Add access to Termpylus code.
    sys.path.append("LOCALPH")

def run_io_loop():
    from Termpylus_core import projects

    def _is_obj(leaf):
        ty = type(leaf)
        return ty not in [str, int, float, bool]
    def _repr1(x): # Wrap objects in strings so that evaling the code doesn't syntax error.
        return repr(projects.cwalk(lambda x: repr(x) if _is_obj(x) else x, x, leaf_only=True))
    def _issym(x): # Is x a symbol?
        x = x.strip()
        for ch in '=+-/*%{}()[] \n':
            if ch in x:
                return False
        return True

    import time
    time.sleep(SLEEPTIME) # Very difficult to understand bug where reading from stdin too early can break pygame when stdin is set to subprocess.PIPE.
    line_bufs = [] # Store up lines for multi-line exec.
    for line in sys.stdin: # Should wait here if there is no stdin. See: https://stackoverflow.com/questions/7056306/python-wait-until-data-is-in-sys-stdin
        line_bufs.append(line)
        if len(line.lstrip()) == len(line): # No indentation.
            try:
                exec('\n'.join(line_bufs))
            except Exception as e:
                print(traceback.format_exc(), file=sys.stderr)
            line_bufs = []
            # Print out any symbols in the line:
            if _issym(line):
                try:
                    print(eval(line))
                except Exception as e:
                    print(traceback.format_exc(), file=sys.stderr)

thread_obj = threading.Thread(target=run_io_loop)
thread_obj.daemon = True
thread_obj.start()
print('Started io thread loop, proceeding to main project; cwd:', os.path.realpath('.'))
#sys.stdout.flush() # One way to flush, but the unbuffered option helps a ton.

############### Termpylus_prepend_END #################
'''.replace('LOCALPH', local_ph).replace('SLEEPTIME',str(sleep_time))
    return txt

class PyProj():
    def __init__(self, origin, dest, run_file, mod_run_file='default', refresh_dt=3600, printouts=False, sleep_time=2, cmd_line_args=None):
        # A non-None github_URL will replace the contents of the folder!
        self.origin = origin # Folder or URL.
        self.dest = dest # Must be a folder.
        self.run_file = run_file
        self.refresh_dt = refresh_dt
        self.last_refresh_time = -1e100
        self.tubo = None # Fills in upon running.
        self._printouts = printouts
        self.mod_run_file = mod_run_file
        if cmd_line_args is None:
            cmd_line_args = []

        if self.origin != self.dest:
            code_in_a_box.download(self.origin, self.dest, clear_folder=False)

        # Prepend the runfile with a loop which in turn handles I/O-as-code on a seperate thread.
        if not mod_run_file:
            return
        run_path = self.dest+'/'+run_file
        contents = file_io.fload(run_path)
        if mod_run_file == 'default':
            if 'Termpylus_prepend_END' not in contents:
                contents1 = get_prepend(sleep_time=sleep_time)+'\n'+contents
            else:
                contents1 = contents
        else:
            contents1 = mod_run_file(contents)
        file_io.fsave(run_path, contents1)
        _gl['active_projs'].append(self)

    def run(self):
        # Launches the program as a subprocess.
        py_path = self.dest+'/'+self.run_file
        # The -u means "unbuffered" and thus will not need flush reminders in said project's code.
        self.tubo = eye_term.MessyPipe(proc_type='python', proc_args=['-u', py_path]+cmd_line_args, printouts=self._printouts, binary_mode=False, working_dir=self.dest)
        self.tubo.ensure_init()

    # Mirror the MessyPipe API:
    def send(self, txt, include_newline=True, suppress_input_prints=False, add_to_packets=True):
        return self.tubo.send(txt, include_newline=include_newline, suppress_input_prints=suppress_input_prints, add_to_packets=add_to_packets)
    def blit(self, include_history=True):
        return self.tubo.blit(include_history=include_history)
    def wait_for(self, txt, include_history=False, timeout=16):
        dt = 0.001
        t = time.time()
        while True:
            if txt in self.tubo.blit(include_history=include_history):
                break
            dt = min(dt*2, 1.0)
            if time.time()-t>timeout:
                raise Exception(f'Wait for exceeded {timeout} second time out.')
            time.sleep(dt)

    def quit(self):
        # Ends the process.
        for i in range(len(_gl['active_projs'])):
            if _gl['active_projs'][i] is self:
                _gl['dead_projs'].append(_gl['active_projs'][i])
                break
        self.tubo.close()

def project_lookup(query_txt):
    # Looks up a project searching by origin, dest folder, etc.
    # A bit of a heuristic here.
    best_match = 0
    best_proj = None
    for pr in _gl['active_projs']:
        match = 0.0
        if query_txt.lower() == pr.origin.lower() or query_txt.lower() == pr.dest.lower():
            match = 1.0
        elif query_txt.lower() in pr.origin.lower() or query_txt.lower() in pr.dest.lower():
            match = 0.5
        if match>best_match+0.01:
            best_match = match
            best_proj = pr

    return best_proj

##### Functions that run on the subprocesses as well as the main process #######
# TODO: is there a better system than having to mirror all of these functions?

def bcast_run(code_txt):
    # Runs code_txt in each active project, waits for the data dump, and evaluates the output.
    # Returns a vector of outputs, one for each active project.
    # (projects have a repl loop that runs in it's own Thread).
    def _rm_empty_lines(txt):
        lines = txt.replace('\r\n','\n').split('\n')
        return '\n'.join(list(filter(lambda l:len(l.strip())>0, lines)))

    n = _gl['num_cmds_total']
    out = []
    unique_tok = 'Termpylus_unique'+str(_gl['num_cmds_total'])
    unique_tok1 = 'T'+unique_tok
    for pr in _gl['active_projs']:
        # Before-and-after buffers:
        pr.send(f"print({unique_tok*2})", include_newline=True)
        pr.wait_for(unique_tok*2, include_history=False)
        pr.send(_rm_empty_lines(txt)+'\n'+f"print({unique_tok1*2})", include_newline=True)
        pr.wait_for(unique_tok1*2, include_history=False)
        result_messy = pr.blit(False)
        result_clean = result_messy.strup().split('\n')[0]
        out.append(eval(result_clean)) # Evaluate the txt into a Python data structure

    _gl['num_cmds_total'] = _gl['num_cmds_total']+1
    return out

def var_watch_add_with_bcast(x):
    # Adds watchers to x (unless already added); x can be a module or var name.
    # Will add to Termpylus as well as all active projects.
    pieces = x.split('.')
    if len(pieces)>1:
        mod_name = '.'.join(pieces[0:-1])
        if mod_name in sys['modules']:
            var_watch.add_fn_watcher(mod_name, pieces[-1], f_code=None)
    if x in sys.modules:
        var_watch.add_module_watchers(x)
    if not x.startswith('Termpylus'): # Subprocesses do not need to add watchers to Termpylus's code base.
        bcast_run(f'from Termpylus_core import projects\nprojects.var_watch_add_with_bcast({x})')

def var_watch_remove_with_bcast(x):
    pieces = x.split('.')
    if len(pieces)>1:
        mod_name = '.'.join(pieces[0:-1])
        if mod_name in sys['modules']:
            var_watch.rm_fn_watcher(mod_name, pieces[-1], f_code=None)
    if x in sys.modules:
        var_watch.add_module_watchers(x)
    if not x.startswith('Termpylus'): # Subprocesses do not need to add watchers to Termpylus's code base.
        bcast_run(f'from Termpylus_core import projects\nprojects.var_watch_remove_with_bcast({x})')

def var_watch_all_with_bcast():
    var_watch.add_all_watchers_global()
    bcast_run(f'from Termpylus_core import projects\nprojects.var_watch_all_with_bcast()')

def var_watch_remove_all_with_bcast():
    var_watch.remove_all_watchers()
    bcast_run(f'from Termpylus_core import projects\nprojects.var_watch_remove_all_with_bcast()')

def startup_cache_with_bcast():
    py_updater.startup_cache_sources()
    bcast_run(f'from Termpylus_core import projects\nprojects.startup_cache_with_bcast()')

def update_user_changed_modules_with_bcast():
    py_updater.update_user_changed_modules()
    bcast_run(f'from Termpylus_core import projects\nprojects.update_user_changed_modules_with_bcast()')

def edits_with_bcast(is_filename):
    # Edits to the source code; only includes edits since project startup.
    eds = var_watch.get_txt_edits() # Each is [mname, fname]+the_edit+[t_now]
    ix = 1 if is_filename else 0

    out = {}
    for ed in eds:
        out[ed[ix]] = out.get(ed[ix], [])
        out[ed[ix]].append(ed[2:])
    outs = bcast_run(f'from Termpylus_core import projects\nprojects.edits_with_bcast({is_filename})')
    for out1 in outs:
        for k in set(out.keys()+out1.keys()):
            out[k] = out.get(k,[])+out1.get(k, [])
    return out

def generic_pythonverse_find_with_bcast(bashy_args, avoid_termpylus=False):
    # Don't move the huge pythonverse directly; instead just send the results.
    x = {}
    for ky in sys.modules.keys():
        if not avoid_termpylus or not k.startswith('Termpylus'):
            x[ky] = sys.modules[ky]
    pythonverse = todict.to_dict(x, output_dict=None, blockset_fn=todict.default_blockset, removeset_fn=todict.module_blockset, d1_override=todict.default_override_to_dict1, level=0)

    results =  dquery.pythonverse_find(*bashy_args, pythonverse_verse=None, exclude_Termpylus=avoid_termpylus)
    resultss = bcast_run(f'from Termpylus_core import projects\nx=projects.generic_pythonverse_find_with_bcast({bashy_args}, avoid_termpylus=True)\nx')
    return [results+[results1 for results1 in resultss]]

def generic_source_find_with_bcast(bashy_args):
    from Termpylus_core import dquery
    out =  dquery.source_find(*bashy_args)
    outs = bcast_run(f'from Termpylus_core import projects\nx=projects.generic_source_find_with_bcast({bashy_args})\nx')
    for outi in outs:
        out = out+outi
    return out
