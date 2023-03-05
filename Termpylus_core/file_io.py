# File io simple wrappers.
import os, io, pathlib, shutil, time
from . import gl_data

printouts = False
debug_restrict_disk_modifications_to_these = None

if 'fileio_globals' not in gl_data.dataset:
    gl_data.dataset['fileio_globals'] = {'original_txts':{}}
fglobals = gl_data.dataset['fileio_globals']

def absolute_path(fname):
    return os.path.realpath(fname).replace('\\','/')

def is_path_absolute(fname):
    # Different rules for linux and windows.
    fname = fname.replace('\\','/')
    linux_abspath = fname[0]=='/'
    win_abspath = len(fname)>2 and fname[1]==':' # C:/path/to/folder
    if linux_abspath or win_abspath: # Two ways of getting absolute paths.
        return True
    return False

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

def is_folder(fname):
    return os.path.isdir(fname)

def contents_on_first_call(fname):
    # The contents of the file on the first time said function was called.
    if fname not in fglobals['original_txts']:
        return contents(fname)
    return fglobals['original_txts'][fname]

def date_mod(fname):
    return os.path.getmtime(fname)

def is_hidden(fname):
    return fname.split('/')[-1][0] == '.'

def _unwindoze_attempt(f, name, tries, retry_delay):
    for i in range(tries):
        try:
            f()
            break
        except PermissionError as e:
            if 'being used by another process' not in str(e):
                f() # actual permission errors.
            if i==tries-1:
                raise Exception('Windoze error: Retried too many times and this file stayed in use:', name)
            print('File-in-use error (will retry) for:', name)
            time.sleep(retry_delay)

def _fsave1(fname, txt, mode, tries=12, retry_delay=1.0):
    # Does not need any enclosing folders to already exist.
    #https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
    def f():
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with io.open(fname, mode=mode, encoding="utf-8") as file_obj:
            file_obj.write(txt)
    _unwindoze_attempt(f, fname, tries, retry_delay)

def fsave(fname, txt, tries=12, retry_delay=1.0):
    _fsave1(fname, txt, "w", tries, retry_delay)

def fdelete(fname, tries=12, retry_delay=1.0):
    # Works on files and folders.
    def f():
        if is_folder(fname):
            shutil.rmtree(fname)
        else:
            os.remove(fname)
    _unwindoze_attempt(f, fname, tries, retry_delay)

def fcreate(fname, is_folder):
    if is_folder:
        folder = fname
    else:
        folder, _ = os.path.split(fname)
    #https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
    if not is_folder:
        with open(fname,'a') as _:
            pass

def fappend(fname, txt):
    _fsave1(fname, txt, "a")

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

def files_in_folder1(fname):
    # Fullpath.
    fname = absolute_path(fname)
    files = os.listdir(fname)
    return [(fname+'/'+file).replace('//','/') for file in files]

def recursive_files(fname, include_folders=False, filter_fn=None, max_folder_depth=65536):
    fname = absolute_path(fname)
    if os.path.isdir(fname):
        files1 = files_in_folder1(fname)
        out = []
        for f in files1:
            if filter_fn is not None and not filter_fn(f):
                continue
            if os.path.isdir(f):
                if include_folders:
                    out.append(f)
                if len(fname.split('/'))<max_folder_depth:
                    out = out+recursive_files(f, include_folders, filter_fn, max_folder_depth)
            else:
                out.append(f)
        return out
    else:
        if filter_fn(fname):
            return [fname]
        else:
            return []

####################################Debug safety features#######################

def _fileallow(fname):
    keeplist = debug_restrict_disk_modifications_to_these
    fname = absolute_path(fname)
    if keeplist is not None:
        if type(keeplist) is str:
            keeplist = [keeplist]
        keeplist = [absolute_path(kl) for kl in keeplist]
        allow = False
        for k in keeplist:
            if fname.startswith(k):
                allow = True
        return allow
    else:
        return True

def gaurded_delete(fname, allow_folders=False):
    # Deleting is dangerous.
    fname = absolute_path(fname)
    if not _fileallow(fname):
        raise Exception('debug_restrict_disk_modifications_to_these is set to: '+str(debug_restrict_disk_modifications_to_these).replace('\\\\','/')+' and disallows deleting this filename: '+fname)
    if os.path.isdir(fname) and not allow_folders:
        raise Exception('Attempt to delete folder (and whats inside) when allow_folders=False.')
    fdelete(fname)

def guarded_create(fname, is_folder):
    # Creating files isn't all that dangerous, but still can be annoying.
    # Skips files that already exist.
    fname = absolute_path(fname)
    if not _fileallow(fname):
        raise Exception('debug_restrict_disk_modifications_to_these is set to: '+str(debug_restrict_disk_modifications_to_these).replace('\\\\','/')+' and disallows creating this filename: '+fname)
    fcreate(fname, is_folder)
    return fname
