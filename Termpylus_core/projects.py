# Handles projects.
import os, time, shutil, re
from Termpylus_extern.waterworks import file_io, eye_term, var_watch, py_updater, colorful, deep_stack
import code_in_a_box, proj
from Termpylus_search import var_metrics

_gl = proj.global_get('Termpylus_proj_globlas', {'alive_projs':[], 'dead_projs':[], 'num_cmds_total':0})
varval_report_wrappers = ['...Termpylus'+'subproc (starts here) Exec result...', '...of Termpylus'+'subproc (ends here) Exec...']

def inner_app_loop(startup_sleep_time=2):
    # Run this from the inner app.
    destroy_unicode_in = False; destroy_unicode_out = False # Unicode should work, these are emergency measures otherwise.
    import sys, traceback
    from Termpylus_extern.waterworks import fittings, global_vars

    # https://stackoverflow.com/questions/16549332/python-3-how-to-specify-stdin-encoding
    # line in sys.stdin is a blocking string of *strings*. But processes generally send bytes to eachother.
    enc = sys.stdin.encoding
    if enc.lower() != 'utf-8':
        sys.stdin.reconfigure(encoding='utf-8')
        print(f'Reconfigured encoding from {enc} to utf-8. Because UTF-8 is that good.')

    def _is_obj(leaf):
        ty = type(leaf)
        return ty not in [str, int, float, bool]
    def _repr1(x): # Wrap objects in strings so that evaling the code doesn't syntax error.
        return repr(fittings.cwalk(lambda x: repr(x) if _is_obj(x) else x, x, leaf_only=True))
    def _nounicode(x):
        # https://stackoverflow.com/questions/20078816/replace-non-ascii-characters-with-a-single-space
        #   (why didn't I think of this!)
        return ''.join([i if ord(i) < 128 else '?U?' for i in x])

    time.sleep(startup_sleep_time) # Very difficult to understand bug where reading from stdin too early can break pygame when stdin is set to subprocess.PIPE.
    py_updater.cache_module_code() # After initial sleep time.

    debug_line_IO = False
    line_bufs = [] # Store up lines for multi-line exec.
    sys.stdin.flush() # Needed?
    for line in sys.stdin: # Waits here if there is no stdin. See: https://stackoverflow.com/questions/7056306/python-wait-until-data-is-in-sys-stdin
        # Lines are type "string".
        #print('Line bytes:', line, [hex(b) for b in line.encode()]) # Debug.
        # No need for global_vars.tprint b/c this is all inside the app.
        if destroy_unicode_in:
            line = _nounicode(line)
        try:
            x = deep_stack.exec_feed(line_bufs, line, sys.modules[__name__].__dict__)
            if x is not None:
                x_txt = _repr1(None if x=='<None>' else x)
                output = varval_report_wrappers[0]+x_txt+varval_report_wrappers[1]
                output = _nounicode(output) if destroy_unicode_out else output
                out_bytes = output.encode('utf-8')
                if debug_line_IO:
                    print('WE HAVE OUTPUT after this line:', line.encode('utf-8'), out_bytes)
                global_vars.bprint(out_bytes)
            elif debug_line_IO:
                print('NO output from this line:', line.encode('utf-8'))
        except Exception as e:
            err_report = traceback.format_exc()
            err_report = _nounicode(err_report) if destroy_unicode_out else err_report
            global_vars.bprint(err_report)
        sys.stdin.flush() # Needed?

def get_prepend(sleep_time=2):
    # Before the main code runs we need to set up.
    local_ph = os.path.realpath('.').replace('\\','/')
    txt = r'''
if __name__ == '__main__':
    import os, sys, traceback, threading, time

    if "LOCALPH" not in sys.path: # Add access to Termpylus code.
        sys.path.append("LOCALPH")
    from Termpylus_extern.waterworks import py_updater
    #sys.stdout.reconfigure(encoding='utf-8')
    from Termpylus_core import projects

    thread_obj = threading.Thread(target=lambda: projects.inner_app_loop(startup_sleep_time=SLEEPTIME))
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
        debug_test_error = True
        if debug_test_error:
            stdout_blit = self.blit(include_history=True, stdout=True, stderr=False)
            stderr_blit = self.blit(include_history=True, stdout=False, stderr=True)
            err_msg = deep_stack.from_stream(stdout_blit, stderr_blit, compress_multible=False, helpful_id=self.tubo.machine_id)
        self.tubo.bubble_stream_errors()

    def launch(self, cmd_line_args=None):
        # Launches the program as a subprocess.
        py_path = self.dest+'/'+self.run_file
        if cmd_line_args is None:
            cmd_line_args = []
        # The -u means "unbuffered" and thus will not need flush reminders in said project's code.
        use_bin = True # Not sure which is better.
        self.tubo = eye_term.MessyPipe(proc_type='python', proc_args=['-u', py_path]+cmd_line_args, printouts=self._printouts, binary_mode=use_bin, working_dir=self.dest)
        self.tubo.flush_stdin = True
        self.tubo.ensure_init()

    # Mirror the MessyPipe API:
    def send(self, txt, include_newline=True, suppress_input_prints=False, add_to_packets=True):
        if self.tubo is None:
            self.launch()
        if type(txt) is str:
            txt = txt.encode('utf-8')
            deebygg = txt.decode('utf-8') # Raise errors in case there is a strange bug.
        if include_newline:
            txt = txt+('\n'.encode('utf-8'))
        out = self.tubo.send(txt, include_newline=False, suppress_input_prints=suppress_input_prints, add_to_packets=add_to_packets)
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
    def wait_for(self, txt, include_history=False, assert_no_exc=False, timeout=8): # The world of "expect".
        dt = 0.001
        t = time.time()
        while True:
            if assert_no_exc:
                self.assert_no_exc()
            bl = self.tubo.blit(include_history=include_history)
            if type(bl) is bytes:
                bl = bl.decode('utf-8')
            if txt in bl:
                break
            if time.time()-t>timeout:
                blit_lengths = [len(self.tubo.blit(include_history=b)) for b in [False, True]]
                raise Exception(f'Wait for "{txt}" exceeded {timeout} second time out; len of blits: {blit_lengths}')
            time.sleep(dt)
            dt = min(dt*2, 1.0)

    def exec(self, code_txt, assert_result=True, str_mode=False): # The API is modified slightly from tubo.API
        from Termpylus_extern.waterworks import global_vars; tprint = global_vars.tprint
        debug_tprint = False
        if not code_txt.endswith('\n'):
            code_txt = code_txt+'\n'
        if debug_tprint:
            tprint('>>>Exec-ing this code:', _gl['num_cmds_total'], code_txt.replace('\n','⏎'), 'error horizion:', self.tubo.error_horizons)
        unique_tok = 'Termpylus_unique'+str(_gl['num_cmds_total'])
        unique_tok1 = 'Unique_Termpylus'+str(_gl['num_cmds_total'])
        _gl['num_cmds_total'] = _gl['num_cmds_total']+1
        self.send(f"\nprint('{unique_tok}'+'{unique_tok}')\n", include_newline=False)
        self.wait_for(unique_tok*2, include_history=False, assert_no_exc=True) # Wait fors have built in asserts that will raise errors if the subprocess raises/prints errors.
        if debug_tprint:
            tprint('000Waited for:', unique_tok*2)
        self.send(code_txt+'\n'+f"print('{unique_tok1}'+'{unique_tok1}')\npass\n", include_newline=False)
        self.wait_for(unique_tok1*2, include_history=False, assert_no_exc=False)
        if debug_tprint:
            tprint('999Waited for:', unique_tok1*2)
        self.assert_no_exc() # Finds and raises an error if exec fails.

        result_messy = self.blit(include_history=False, stdout=True, stderr=True)
        if type(result_messy) is bytes:
            result_messy = result_messy.decode('utf-8')
        messy_pieces = result_messy.strip().split(varval_report_wrappers[0])

        if varval_report_wrappers[0] not in result_messy:
            if assert_result:
                raise Exception(f'No output seems to have been created; disable assert_result if no result is needed')
            else:
                return None

        clean_pieces = [messy_piece.split(varval_report_wrappers[1])[0] for messy_piece in messy_pieces[1:]]
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
                _gl['alive_projs'][i] = None
                break
        _gl['alive_projs'] = list(filter(lambda x:x, _gl['alive_projs']))
        self.send('\nsys.exit()\n\n\n')
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
    quit_these = _gl['alive_projs'].copy()
    for ap in quit_these:
        ap.quit()
    return len(quit_these)

##### Functions that run on the subprocesses as well as the main process #######
# TODO: is there a better system than having to mirror all of these functions?

def bcast_run(code_txt, wait=True, assert_result=True):
    # Runs code_txt in each active project, waits for the data dump, and evaluates the output.
    # Returns a vector of outputs, one for each active project.
    # (projects have a repl loop that runs in it's own Thread).

    out = []
    for pr in _gl['alive_projs']: # TODO: concurrency even if "wait" is True.
        if wait:
            out.append(pr.exec(code_txt, assert_result=assert_result))
        else:
            pr.send(code_txt, include_newline=True)
            out.append(None)

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
    py_updater.cache_module_code()
    bcast_run(f'from Termpylus_core import projects\nprojects.startup_cache_with_bcast()', wait=False)

def update_user_changed_modules_with_bcast(update_on_first_see=True):
    py_updater.update_user_changed_modules(update_on_first_see=update_on_first_see)
    bcast_run(f'from Termpylus_core import projects\nprojects.update_user_changed_modules_with_bcast(update_on_first_see={update_on_first_see})\nTrue', wait=True)

def edits_with_bcast(is_filename, depth_first=True):
    # Edits to the source code; only includes edits since project startup.
    # depth_first is a lot less important than it is on the generic finds.
    eds = var_watch.get_txt_edits() # Each is [mname OR fname]+the_edit+[t_now]
    ix = 1 if is_filename else 0

    out = {}
    for ed in eds:
        out[ed[ix]] = out.get(ed[ix], [])
        out[ed[ix]].append(ed[2:])
    outs = bcast_run(f'from Termpylus_core import projects\nedits_this_proj=projects.edits_with_bcast({is_filename}, depth_first={depth_first})\nedits_this_proj')
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

    results =  var_metrics.pythonverse_find(*bashy_args, pythonverse_verse=None, exclude_Termpylus=avoid_termpylus)
    # Set avoid_termpylus to True to avoid redundent calls:
    resultss = bcast_run(f'from Termpylus_core import projects\nx=projects.generic_pythonverse_find_with_bcast({bashy_args}, avoid_termpylus=True, depth_first={depth_first})\nx')

    return sum(resultss+[results] if depth_first else [results]+resultss, [])

def generic_source_find_with_bcast(bashy_args, depth_first=True):
    from Termpylus_core import dquery
    results =  var_metrics.source_find(*bashy_args)
    resultss = bcast_run(f'from Termpylus_core import projects\nx=projects.generic_source_find_with_bcast({bashy_args}, depth_first={depth_first})\nx')

    return sum(resultss+[results] if depth_first else [results]+resultss, [])
