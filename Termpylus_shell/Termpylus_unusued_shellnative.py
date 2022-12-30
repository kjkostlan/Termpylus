# This was quite the learning expirance to work with processes.
# See also: https://stackoverflow.com/questions/24640079/process-stdout-readline-hangs-how-to-use-it-properly
#           https://stackoverflow.com/questions/28616018/multiple-inputs-and-outputs-in-python-subprocess-communicate
import subprocess, threading, os
import time

class Shell:
    def __init__(self):

        if os.name == 'nt': # Windows
            proc = 'cmd'
        else:
            proc = 'bash'

        out = {}

        big_question_do_we_shell = True
        universal_newlines = False # Makes things worse.

        p = subprocess.Popen([proc], stderr=subprocess.PIPE, shell=big_question_do_we_shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=universal_newlines)
        self.proc = p
        self.outputs = [] # [message, is_error, input_ix]
        self.listenerkill = False
        self.input_ix = 0
        self.str_mode = universal_newlines
        self.len_outputpairs = -1

        #https://stackoverflow.com/questions/9673730/interacting-with-bash-from-python
        def read_stdouterr(is_err):
            while not self.listenerkill:
                msg = p.stdout.readline()
                if type(msg) is not str:
                    msg = msg.decode()
                #if len(msg)>0:
                self.outputs.append([msg, is_err, self.input_ix])
        def read_stdout(): #Exactly what keeps these loops from running constantly?
            read_stdouterr(False)
        def read_stderr():
            read_stdouterr(True)
        threading.Thread(target=read_stdout).start()
        threading.Thread(target=read_stderr).start()

    def send(self, input, include_newline=True):
        if len(input)>0:
            if include_newline and input[-1] != '\n':
                input = input+'\n'
            if not self.str_mode:
                input = input.encode()
                #str_mode
            self.proc.stdin.write(input)
            self.proc.stdin.flush()

    def exit_shell(self):
        self.listenerkill = True
        self.proc.kill()

    def add_update_listener(self, f, dt=0.0625):
        # Calls f when shell updates, and once upon adding.

        def listenloop():
            while not self.listenerkill:
                n0 = self.len_outputpairs
                n = len(self.outputs)
                if n != n0:
                    self.len_outputpairs = n
                    f()
                time.sleep(dt)
        threading.Thread(target=listenloop).start()

    def autocorrect(self, input):
        return input

