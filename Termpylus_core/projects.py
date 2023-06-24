# Handles projects.
import sys, os, time, shutil, re
import code_in_a_box
from Termpylus_shell import bashy_cmds, shellpython
from Termpylus_extern.waterworks import file_io, eye_term

def get_prepend(sleep_time=2):
    # Before the main code runs we need to set up.
    local_ph = os.path.realpath('.').replace('\\','/')
    txt = '''
import os, sys, traceback, threading

if "LOCALPH" not in sys.path: # Add access to Termpylus code.
    sys.path.append("LOCALPH")

def run_io_loop():
    import time
    time.sleep(SLEEPTIME) # Very difficult to understand bug where reading from stdin too early can break pygame when stdin is set to subprocess.PIPE.
    for line in sys.stdin: # Should wait here if there is no stdin. See: https://stackoverflow.com/questions/7056306/python-wait-until-data-is-in-sys-stdin
        try:
            x = exec(str(line)) # Is line already a str?
            print(x, file=sys.stdout)
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
    def __init__(self, origin, dest, run_file, mod_run_file='default', refresh_dt=3600, printouts=False, sleep_time=2):
        # A non-None github_URL will replace the contents of the folder!
        self.origin = origin # Folder or URL.
        self.dest = dest # Must be a folder.
        self.run_file = run_file
        self.refresh_dt = refresh_dt
        self.last_refresh_time = -1e100
        self.tubo = None # Fills in upon running.
        self._printouts = printouts
        self.mod_run_file = mod_run_file

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

    def run(self):
        # Launches the program as a subprocess.
        py_path = self.dest+'/'+self.run_file
        # The -u means "unbuffered" and thus will not need flush reminders in said project's code.
        self.tubo = eye_term.MessyPipe(proc_type='python', proc_args=['-u', py_path], printouts=self._printouts, binary_mode=False, working_dir=self.dest)
        self.tubo.ensure_init()

    # Mirror the MessyPipe API:
    def send(self, txt, include_newline=True, suppress_input_prints=False, add_to_packets=True):
        return self.tubo.send(txt, include_newline=include_newline, suppress_input_prints=suppress_input_prints, add_to_packets=add_to_packets)
    def blit(self, include_history=True):
        return self.tubo.blit(include_history=include_history)
