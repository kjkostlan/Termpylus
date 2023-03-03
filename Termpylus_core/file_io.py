# File io simple wrappers.
import os, io
from . import gl_data

printouts = False

if 'fileio_globals' not in gl_data.dataset:
    gl_data.dataset['fileio_globals'] = {'original_txts':{}}
fglobals = gl_data.dataset['fileio_globals']

def contents(fname):
    if not os.path.isfile(fname):
        return None
    with io.open(fname, mode="r", encoding="utf-8") as file_obj:
        try:
            x = file_obj.read()
        except UnicodeDecodeError:
            raise Exception('No UTF-8 for:', fname)
        out = x.replace('\r\n','\n')
        if fname not in fglobals['original_txts']:
            fglobals['original_txts'][fname] = out
        return out

def contents_on_first_call(fname):
    # The contents of the file on the first time said function was called.
    if fname not in fglobals['original_txts']:
        return contents(fname)
    return fglobals['original_txts'][fname]

def date_mod(fname):
    return os.path.getmtime(fname)

def fsave1(fname, txt, mode):
    #https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    with io.open(fname, mode=mode, encoding="utf-8") as file_obj:
        file_obj.write(txt)

def fsave(fname, txt):
    fsave1(fname, txt, "w")

def fappend(fname, txt):
    fsave1(fname, txt, "a")

def clear_pycache(filename):
    # This can intefere with updating.
    cachefolder = os.path.dirname(filename)+'/__pycache__'
    leaf = os.path.basename(filename).replace('.py','')
    if os.path.isdir(cachefolder):
        leaves = os.listdir(cachefolder)
        for l in leaves:
            if leaf in l:
                if printouts:
                    print('Deleting cached file:', cachefolder+'/'+l)
                os.remove(cachefolder+'/'+l)
