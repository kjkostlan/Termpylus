# Handles projects.
import sys, os, time, shutil, re
import code_in_a_box, proj
from Termpylus_extern.waterworks import file_io, eye_term, var_watch, py_updater, colorful, deep_stack

_gl = proj.global_get('Termpylus_proj_globlas', {'alive_projs':[], 'dead_projs':[], 'num_cmds_total':0})

def get_prepend(sleep_time=2):
    # Before the main code runs we need to set up.
    local_ph = os.path.realpath('.').replace('\\','/')
    txt = r'''
if __name__ == '__main__':
    import os, sys, traceback, threading, time

    if "LOCALPH" not in sys.path: # Add access to Termpylus code.
        sys.path.append("LOCALPH")
    from Termpylus_extern.waterworks import py_updater
    print('ENCODING FUN DELUXE:', sys.stdout.encoding)
    #sys.stdout.reconfigure(encoding='utf-8')

    def run_io_loop():
        from Termpylus_core import projects
        from Termpylus_extern.waterworks import deep_stack

        time.sleep(SLEEPTIME) # Very difficult to understand bug where reading from stdin too early can break pygame when stdin is set to subprocess.PIPE.
        py_updater.startup_cache_sources() # After initial sleep time.

        line_bufs = [] # Store up lines for multi-line exec.
        print("ABOUT TO ENTER WAIT FOR INPUT LOOP")
        sys.stdin.flush() # Needed?
        for line in sys.stdin: # Waits here if there is no stdin. See: https://stackoverflow.com/questions/7056306/python-wait-until-data-is-in-sys-stdin
            deep_stack.exec_feed(line_bufs, line, sys.modules[__name__].__dict__)
            sys.stdin.flush() # Needed?

    thread_obj = threading.Thread(target=run_io_loop)
    thread_obj.daemon = True
    thread_obj.start()
    print('Started io thread loop, proceeding to main project; cwd:', os.path.realpath('.'))
    #sys.stdout.flush() # One way to flush, but the unbuffered option helps a ton.

############### Termpylus_prepend_END #################
'''.replace('LOCALPH', local_ph).replace('SLEEPTIME',str(sleep_time))
    return txt

class PyProj():
    def __init__(self, origin, dest, run_file, mod_run_file='default', refresh_dt=3600, printouts=False, sleep_time=2, cmd_line_args=None, name='PyProj', github_branch=None):
        # A non-None github_URL will replace the contents of the folder!
        self.origin = origin # Folder or URL.
        self.dest = dest # Must be a folder.
        self.run_file = run_file
        self.refresh_dt = refresh_dt
        self.last_refresh_time = -1e100
        self.tubo = None # Fills in upon running.
        self._printouts = printouts
        self.mod_run_file = mod_run_file
        self.name = name
        if cmd_line_args is None:
            cmd_line_args = []

        if self.origin != self.dest:
            code_in_a_box.download(self.origin, self.dest, clear_folder=False, branch=github_branch)

        # Prepend the runfile with a loop which in turn handles I/O-as-code on a seperate thread.
        if not mod_run_file:
            return
        run_path = self.dest+'/'+run_file
        contents = file_io.fload(run_path)
        if contents is None:
            raise Exception('Cannot find file: '+self.dest+'/'+run_file)
        if mod_run_file == 'default':
            if 'Termpylus_prepend_END' not in contents:
                contents1 = get_prepend(sleep_time=sleep_time)+'\n'+contents
            else:
                contents1 = contents
        else:
            contents1 = mod_run_file(contents)
        file_io.fsave(run_path, contents1)
        _gl['alive_projs'].append(self)

    def assert_no_exc(self):
        self.tubo.machine_id = self.name # A kludge to put self.name into the error reports.
        self.tubo.bubble_stream_errors()

    def launch(self, cmd_line_args=None):
        # Launches the program as a subprocess.
        py_path = self.dest+'/'+self.run_file
        if cmd_line_args is None:
            cmd_line_args = []
        # The -u means "unbuffered" and thus will not need flush reminders in said project's code.
        self.tubo = eye_term.MessyPipe(proc_type='python', proc_args=['-u', py_path]+cmd_line_args, printouts=self._printouts, binary_mode=False, working_dir=self.dest)
        self.tubo.flush_stdin = True
        self.tubo.ensure_init()

    # Mirror the MessyPipe API:
    def send(self, txt, include_newline=True, suppress_input_prints=False, add_to_packets=True):
        if self.tubo is None:
            self.launch()
        out = self.tubo.send(txt, include_newline=include_newline, suppress_input_prints=suppress_input_prints, add_to_packets=add_to_packets)
        for i in range(8):
            try:
                self.tubo.proc_obj.stdin.flush() # Seems to be needed.
                return out
            except Exception as e:
                print('Waiting for stdin flush to work.')
                if i==8:
                    raise e
                time.sleep(1)
        raise Exception('The stdin flush never worked, did the process quit?')
    def blit(self, include_history=True, stdout=True, stderr=True):
        if self.tubo is None:
            self.launch()
        return self.tubo.blit(include_history=include_history, stdout=stdout, stderr=stderr)
    def wait_for(self, txt, include_history=False, timeout=8): # The world of "expect".
        dt = 0.001
        t = time.time()
        while True:
            self.assert_no_exc()
            recent_blit = self.tubo.blit(include_history=include_history)
            if txt in recent_blit:
                break
            if time.time()-t>timeout:
                raise Exception(f'Wait for "{txt}" exceeded {timeout} second time out; len of blit since last command: {len(recent_blit)}')
            time.sleep(dt)
            dt = min(dt*2, 1.0)

    def exec(self, code_txt, assert_result=True, str_mode=False): # The API is modified slightly from tubo.API
        unique_tok = 'Termpylus_unique'+str(_gl['num_cmds_total'])
        unique_tok1 = 'T'+unique_tok
        self.send(f"print('{unique_tok*2}')\n", include_newline=True)
        self.wait_for(unique_tok*2, include_history=False) # Wait fors have built in asserts that will raise errors if the subprocess raises/prints errors.
        self.send(code_txt+'\n'+f"print('{unique_tok1*2}')\npass", include_newline=True)
        self.wait_for(unique_tok1*2, include_history=False)
        result_messy = self.blit(include_history=False, stdout=True, stderr=True).strip()
        messy_pieces = result_messy.split(deep_stack.varval_report_wrappers[0])

        if deep_stack.varval_report_wrappers[0] not in result_messy:
            if assert_result:
                raise Exception(f'No output seems to have been created; disable assert_result if no result is needed')
            else:
                return None

        clean_pieces = [messy_piece.split(deep_stack.varval_report_wrappers[1])[0] for messy_piece in messy_pieces[1:]]

        out = []
        for clean_piece in clean_pieces:
            if len(clean_piece.strip())>0:
                try:
                    out.append(clean_piece if str_mode else eval(clean_piece)) # Evaluate the txt into a Python data structure (or raise an error if it cant be evaled)
                except Exception as e:
                    if len(clean_piece)<1024:
                        raise Exception('Eval return obj from process error: '+str(e)+' INPUT '+'"'+code_txt+'"'+' OUTPUT '+'"'+clean_piece+'"')
                    else:
                        raise Exception(f'Eval large (n={len(clean_piece)}) return obj from process error: '+str(e))

        if assert_result and len(out)==0: # Each result is in between deep_stack.varval_report_wrapper tokens
            self.assert_no_exc()
            _txt = '(non-empty)' if len(clean_pieces)>0 else ''
            raise Exception(f'No{_txt} output seems to have been created; disable assert_result if no result is needed')

        # 0 outputs = None, 1 = the output, 2+ = a list of each output:
        if len(out)==0:
            return None
        return out if len(out)>1 else out[0]

    def quit(self):
        # Ends the process.
        for i in range(len(_gl['alive_projs'])):
            if _gl['alive_projs'][i] is self:
                _gl['dead_projs'].append(_gl['alive_projs'][i])
                break
        if self.tubo is not None:
            self.tubo.close()

################################################################################

def project_lookup(query_txt):
    # Looks up a project searching by origin, dest folder, etc.
    # A bit of a heuristic here.
    best_match = 0
    best_proj = None
    for pr in _gl['alive_projs']:
        match = 0.0
        if query_txt.lower() == pr.origin.lower() or query_txt.lower() == pr.dest.lower():
            match = 1.0
        elif query_txt.lower() in pr.origin.lower() or query_txt.lower() in pr.dest.lower():
            match = 0.5
        if match>best_match+0.01:
            best_match = match
            best_proj = pr

    return best_proj

def quit_all():
    # Quits all projects, removing them from 'active' to 'dead'
    for ap in _gl['alive_projs']:
        ap.quit()
        _gl['dead_projs'].append(ap)
    _gl['alive_projs'] = []

##### Functions that run on the subprocesses as well as the main process #######
# TODO: is there a better system than having to mirror all of these functions?

def bcast_run(code_txt, wait=True):
    # Runs code_txt in each active project, waits for the data dump, and evaluates the output.
    # Returns a vector of outputs, one for each active project.
    # (projects have a repl loop that runs in it's own Thread).

    n = _gl['num_cmds_total']
    out = []
    unique_tok = 'Termpylus_unique'+str(_gl['num_cmds_total'])
    unique_tok1 = 'T'+unique_tok
    code_txt = code_txt+'\npass' # A non-indented lines tells the process it is ready to eval the growing block of code.
    for pr in _gl['alive_projs']: # TODO: concurrency.
        if wait:
            out.append(pr.exec(code_txt))
        else:
            pr.send(code_txt, include_newline=True)
            out.append(None)

    _gl['num_cmds_total'] = _gl['num_cmds_total']+1
    return out

def var_watch_add_with_bcast(var_or_modulename):
    # Adds watchers to x (unless already added); x can be a module or var name.
    # Will add to Termpylus as well as all active projects.
    pieces = var_or_modulename.split('.')
    if len(pieces)>1:
        mod_name = '.'.join(pieces[0:-1])
        if mod_name in sys['modules']:
            var_watch.add_fn_watcher(mod_name, pieces[-1], f_code=None)
    if x in sys.modules:
        var_watch.add_module_watchers(var_or_modulename)
    if not x.startswith('Termpylus'): # Subprocesses do not need to add watchers to Termpylus's code base.
        bcast_run(f'from Termpylus_core import projects\nprojects.var_watch_add_with_bcast({x})', wait=False)

def var_watch_remove_with_bcast(var_or_modulename):
    pieces = var_or_modulename.split('.')
    if len(pieces)>1:
        mod_name = '.'.join(pieces[0:-1])
        if mod_name in sys['modules']:
            var_watch.rm_fn_watcher(mod_name, pieces[-1], f_code=None)
    if x in sys.modules:
        var_watch.add_module_watchers(var_or_modulename)
    if not x.startswith('Termpylus'): # Subprocesses do not need to add watchers to Termpylus's code base.
        bcast_run(f'from Termpylus_core import projects\nprojects.var_watch_remove_with_bcast({x})', wait=False)

def var_watch_add_all_with_bcast():
    var_watch.add_all_watchers_global()
    bcast_run(f'from Termpylus_core import projects\nprojects.var_watch_all_with_bcast()', wait=False)

def var_watch_remove_all_with_bcast():
    var_watch.remove_all_watchers()
    bcast_run(f'from Termpylus_core import projects\nprojects.var_watch_remove_all_with_bcast()', wait=False)

def startup_cache_with_bcast():
    py_updater.startup_cache_sources()
    bcast_run(f'from Termpylus_core import projects\nprojects.startup_cache_with_bcast()', wait=False)

def update_user_changed_modules_with_bcast(update_on_first_see=True):
    py_updater.update_user_changed_modules(update_on_first_see=update_on_first_see)
    bcast_run(f'from Termpylus_core import projects\nprojects.update_user_changed_modules_with_bcast(update_on_first_see={update_on_first_see})', wait=False)

def edits_with_bcast(is_filename, depth_first=True):
    # Edits to the source code; only includes edits since project startup.
    # depth_first is a lot less important than it is on the generic finds.
    eds = var_watch.get_txt_edits() # Each is [mname OR fname]+the_edit+[t_now]
    ix = 1 if is_filename else 0

    out = {}
    for ed in eds:
        out[ed[ix]] = out.get(ed[ix], [])
        out[ed[ix]].append(ed[2:])
    outs = bcast_run(f'from Termpylus_core import projects\nx=projects.edits_with_bcast({is_filename}, depth_first={depth_first})\nx')
    for out1 in outs:
        for k in list(out.keys())+list(out1.keys()):
            out[k] = out1.get(k,[])+out.get(k, []) if depth_first else out.get(k,[])+out1.get(k, [])
    return out

def generic_pythonverse_find_with_bcast(bashy_args, avoid_termpylus=False, depth_first=True):
    # Don't move the huge pythonverse directly; instead just send the results.
    x = {}
    for ky in sys.modules.keys():
        if not avoid_termpylus or not k.startswith('Termpylus'):
            x[ky] = sys.modules[ky]
    pythonverse = todict.to_dict(x, output_dict=None, blockset_fn=todict.default_blockset, removeset_fn=todict.module_blockset, d1_override=todict.default_override_to_dict1, level=0)

    results =  dquery.pythonverse_find(*bashy_args, pythonverse_verse=None, exclude_Termpylus=avoid_termpylus)
    # Set avoid_termpylus to True to avoid redundent calls:
    resultss = bcast_run(f'from Termpylus_core import projects\nx=projects.generic_pythonverse_find_with_bcast({bashy_args}, avoid_termpylus=True, depth_first={depth_first})\nx')

    return sum(resultss+[results] if depth_first else [results]+resultss, [])

def generic_source_find_with_bcast(bashy_args, depth_first=True):
    from Termpylus_core import dquery
    results =  dquery.source_find(*bashy_args)
    resultss = bcast_run(f'from Termpylus_core import projects\nx=projects.generic_source_find_with_bcast({bashy_args}, depth_first={depth_first})\nx')

    return sum(resultss+[results] if depth_first else [results]+resultss, [])
