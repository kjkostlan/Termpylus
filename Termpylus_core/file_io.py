# File io simple wrappers.
import os, io
from . import gl_data

printouts = False
debug_restrict_disk_modifications_to_these = None

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

def fdelete(fname):
    TODO

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
                    out = out+recursive_files_core(f, include_folders, filter_fn, max_folder_depth)
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
        keeplist = [os.path.realpath(kl).replace('\\','/') for kl in keeplist]
        allow = False
        for k in keeplist:
            if fname.startswith(k):
                allow = True
        return allow
    else:
        return True

def gaurded_delete(fname, allow_folders=False):
    # Deleting is dangerous.
    if not _fileallow(fname):
        raise Exception('debug_restrict_disk_modifications_to_these is set to: '+str(debug_restrict_disk_modifications_to_these).replace('\\\\','/')+' and disallows deleting this filename: '+fname)
    if os.path.isdir(fname) and not allow_folders:
        raise Exception('Attempt to delete folder (and whats inside) when allow_folders=False.')
    fdelete(fname)

def guarded_create(fname, is_folder):
    # Creating files isn't all that dangerous, but still can be annoying.
    # Skips files that already exist.
    if not _fileallow(fname):
        raise Exception('debug_restrict_disk_modifications_to_these is set to: '+str(debug_restrict_disk_modifications_to_these).replace('\\\\','/')+' and disallows creating this filename: '+fname)
    fcreate(fname, is_folder)
    return fname
