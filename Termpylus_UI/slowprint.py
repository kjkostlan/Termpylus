# Functions to print slowly.
import time, threading, io, os
import multiprocessing as mp #https://docs.python.org/3/library/multiprocessing.html#the-process-class

def slowprint(*args, interval=0.5, main_printer=None):
    # Only once per half second. Safe to use inside busy loops.
    t1 = time.time()
    if t1>main_printer.last_slow_print_time[0]+interval:
        main_printer.last_slow_print_time[0] = t1
        print(*args)

def last_impression_print(*args, main_printer=None):
    # Use this function to catch freeze-bugs.
    args1 = ['【 t: '+str(time.time())+'】']+list(args)
    main_printer.last_imp_obj[0] = args1

def _filewrite_core(lines, mode):
    fname = './_log.txt'
    with io.open(fname, mode=mode, encoding="utf-8") as file_obj:
        file_obj.write('\n'.join(lines)+'\n')

def _fileprint(args, mode='', subprocess_pipe=None):
    # Print to a log file.
    pieces = [str(x) for x in args]
    if subprocess_pipe is None: # immediate write, but may be slow since it doesn't chunk.
        _filewrite_core([' '.join(pieces)])
    else: # Go into the pipe. The power of python pickling!
        args1 = [str(mode)]+pieces
        subprocess_pipe.send(args1)

def subprocess_loop(a_pipe):
    while True:
        time.sleep(0.25)
        t0 = time.time()
        lines = []
        while a_pipe.poll():
            lines.append(a_pipe.recv())
        wipe = False
        lines1 = []
        for l in lines:
            l1 = ' '.join([str(x) for x in l[1:]])
            if l[0]=='w':
                lines1 = [l1]
                wipe = True
            else:
                lines1.append(l1)
        if len(lines1)>0:
            _filewrite_core(lines1, 'w' if wipe else 'a')
            print('Print subprocess loop t=', time.time()-t0, ' # lines:', len(lines))

def fileprint(*args, main_printer='None or a PrinterState'):
    # Print to a log file.
    _fileprint(args, 'a', None if main_printer is None else main_printer.pipe_endA)

def fileprint1(*args, main_printer='None or a PrinterState'):
    # Wipe then print to a log file.
    _fileprint(args, 'w', None if main_printer is None else main_printer.pipe_endA)

class PrinterState():
    def __init__(self):
        self.last_slow_print_time = [0.0]
        self.last_imp_obj = [None]
        def print_loop():
            while True:
                if self.last_imp_obj[0] is not None:
                    #print('About to lastimp print something!')
                    #time.sleep(0.01)
                    print(*self.last_imp_obj[0])
                    self.last_imp_obj[0] = None
                #else:
                #    print('Empty loop t=:', time.time())
                time.sleep(0.25)
        self.slowprint_thread = threading.Thread(target=print_loop, args=())
        self.slowprint_thread.start()
        self.pipe_endA, self.pipe_endB = mp.Pipe()
        self.sproc = mp.Process(target=subprocess_loop, args=[self.pipe_endB])
        self.sproc.start()

'''
# DEBUG code that makes it easier to call slowprint from another module.
from Termpylus_UI import slowprint
_sprts = [slowprint.last_impression_print, slowprint.fileprint, slowprint.fileprint1]
_sprt = _sprts[1] # Change this ix to change which one is used.
def sprt(*args):
    _sprt(*args, main_printer=sys.modules['__main__'].print_state_singleton)
'''