# Python shell with some wrappers for simple linux commands.
# It holds a current working directory to feel shell-like.
import sys

def str1(x):
    sx = str(x)
    if len(sx)>512:
        sx = '<big thing>'
    return sx

def _module_strs():
    modl = sys.modules[__name__]
    return dict(zip(modl.__dict__.keys(), [str(x) for x in modl.__dict__.values()]))

class Shell:
    def __init__(self):

        self.cur_dir = '.' #TODO: default directory.
        self.outputs = [] # [message, is_error, input_ix]
        self.input_ix = 0
        self.listenerf = None

    def autocorrect(self, input):
        # TODO: simple shell commands with the path.
        return input

    def send(self, input, include_newline=True):
        input = input.strip()
        if len(input)>0:
            strs0 = _module_strs()
            err = ''
            try:
                #https://stackoverflow.com/questions/23168282/setting-variables-with-exec-inside-a-function
                exec(input, globals(), globals())
                #print('Exed input:', input, 'dict:', sys.modules[__name__].__dict__.keys())
            except Exception as e:
                err = str(repr(e))

            strs1 = _module_strs()
            vars_set = ''
            for ky in strs1.keys():
                if strs1[ky] != strs0.get(ky, None):
                    vars_set = vars_set+'\n'+ky+' = '+str1(eval(ky))
            if len(vars_set)==0 and len(err)==0:
                vars_set = 'Command succeeded'

            if len(vars_set)>0:
                self.outputs.append([vars_set+'\n', False, self.input_ix])
            if len(err)>0:
                self.outputs.append([err+'\n', True, self.input_ix])

            self.listenerf() #Trigger it manually (since there is no IO stream).
            self.input_ix = self.input_ix+1

    def exit_shell(self):
        pass

    def add_update_listener(self, f, dt=0.0625):
        self.listenerf = f

