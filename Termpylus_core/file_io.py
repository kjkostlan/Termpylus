# Simple, error resistant file wrappers which keep track of the old files
import os, io, pathlib, shutil, time, stat
from . import gl_data

printouts = False
debug_restrict_disk_modifications_to_these = None

if 'fileio_globals' not in gl_data.dataset:
    ph = os.path.realpath('.').replace('\\','/')
    gl_data.dataset['fileio_globals'] = {'original_txts':{},
                                         'original_cwd':ph,
                                         'user_paths':[ph],
                                         'checkpoints':{},
                                         'created_files':set()}
fglobals = gl_data.dataset['fileio_globals']

################################# Pathing ######################################

def is_path_absolute(fname):
    # Different rules for linux and windows.
    fname = fname.replace('\\','/')
    linux_abspath = fname[0]=='/'
    win_abspath = len(fname)>2 and fname[1]==':' # C:/path/to/folder
    if linux_abspath or win_abspath: # Two ways of getting absolute paths.
        return True
    return False

def user_paths():
    return fglobals['user_paths'].copy()

def termp_abs_path(fname): #fname = file_io.Termp_abs_path(fname)
    # The absolute path assuming the working directory is the Termpylus project folder.
    # (the working directory changes to the projects directory when running a project).
    # (here realpath is used to make an absolute path absolute).
    if is_path_absolute(fname):
        return os.path.realpath(fname).replace('\\','/')
    out = os.path.realpath(fglobals['original_cwd']+'/'+fname).replace('\\','/')
    if not is_path_absolute(out):
        raise Exception('Output path not absolute assert bug in this code.')
    return out

#####################################Querying###################################

def is_folder(fname):
    fname = termp_abs_path(fname)
    return os.path.isdir(fname)

def files_in_folder1(fname): # Returns full absolute paths.
    fname = termp_abs_path(fname)
    files = os.listdir(fname)
    return [(fname+'/'+file).replace('//','/') for file in files]

def recursive_files(fname, include_folders=False, filter_fn=None, max_folder_depth=65536):
    fname = termp_abs_path(fname)
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

####################################Loading#####################################

def contents(fname):
    fname = termp_abs_path(fname)
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
    fname = termp_abs_path(fname)
    # The contents of the file on the first time said function was called.
    # OR just before the first time the file was saved.
    if fname not in fglobals['original_txts']:
        txt = contents(fname)
        if txt is not None:
            fglobals['original_txts'][fname] = txt
        return txt
    return fglobals['original_txts'][fname]

def date_mod(fname):
    fname = termp_abs_path(fname)
    return os.path.getmtime(fname)

def is_hidden(fname):
    fname = termp_abs_path(fname)
    return fname.split('/')[-1][0] == '.'

#####################################Saving#####################################

def _update_checkpoints_before_saving(fname):
    fname = termp_abs_path(fname)
    if len(fglobals['checkpoints'])==0:
        return
    txt = contents(fname) # May be None, which means reverting = deleting this file.
    for k in fglobals['checkpoints'].keys():
        if fname not in fglobals['checkpoints'][k]:
            fglobals['checkpoints'][k][fname] = txt

def _unwindoze_attempt(f, name, tries, retry_delay):
    for i in range(tries):
        try:
            f()
            break
        except PermissionError as e:
            if 'being used by another process' not in str(e):
                f() # Throw actual permission errors.
            if i==tries-1:
                raise Exception('Windoze error: Retried too many times and this file stayed in use:', name)
            print('File-in-use error (will retry) for:', name)
            time.sleep(retry_delay)

def _fsave1(fname, txt, mode, tries=12, retry_delay=1.0):
    # Does not need any enclosing folders to already exist.
    #https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
    fname = termp_abs_path(fname)
    def f():
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with io.open(fname, mode=mode, encoding="utf-8") as file_obj:
            file_obj.write(txt)
    _unwindoze_attempt(f, fname, tries, retry_delay)

def fsave(fname, txt, tries=12, retry_delay=1.0):
    # Automatically stores the original txts.
    fname = termp_abs_path(fname)
    _update_checkpoints_before_saving(fname)
    if os.path.exists(fname):
        contents_on_first_call(fname) # Save the old contents.
    else:
        fglobals.created_files.add(fname)
    _fsave1(fname, txt, "w", tries, retry_delay)

def fcreate(fname, is_folder):
    # Creates an empty file.
    fname = termp_abs_path(fname)
    if not os.path.exists(fname):
        fglobals.created_files.add(fname)
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
    fname = termp_abs_path(fname)
    if len(fglobals['checkpoints'])>0: # Requires a load+save.
        fsave(fname, contents(fname)+txt)
    else:
        _fsave1(fname, txt, "a")

def save_checkpoint(name):
    # Save a checkpoint which can be reverted to. Overwrite if name already exists.
    fglobals['checkpoints'][name] = {}

##############################Deleting############################

def fdelete(fname, tries=12, retry_delay=1.0):
    # Can be reverted IF there is a checkpoint saved.
    fname = termp_abs_path(fname)
    _update_checkpoints_before_saving(fname)
    version2 = False # (I think) V1 and V2 are equivalent.

    # Works on files and folders.
    if version2: #https://stackoverflow.com/questions/4829043/how-to-remove-read-only-attrib-directory-with-python-in-windows
        def f():
            if is_folder(fname):
                for root, dirs, files in os.walk(fname):
                    for fname1 in files:
                        full_path = root+'/'+fname1
                        os.chmod(full_path ,stat.S_IWRITE)
            shutil.rmtree(fname)
    else: #https://stackoverflow.com/questions/1889597/deleting-read-only-directory-in-python
        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE) # rmtree can't remove internal read-only files, but the explorer can. This will remov read-only related errors.
            func(path)
        def f():
            if not os.path.exists(fname):
                return
            if is_folder(fname):
                shutil.rmtree(fname, onerror=remove_readonly)
            else:
                os.remove(fname)
    _unwindoze_attempt(f, fname, tries, retry_delay)

def clear_pycache(fname):
    fname = termp_abs_path(fname)
    # This can intefere with updating.
    cachefolder = os.path.dirname(fname)+'/__pycache__'
    leaf = os.path.basename(fname).replace('.py','').replace('\\','/')
    if os.path.isdir(cachefolder):
        leaves = os.listdir(cachefolder)
        for l in leaves:
            if leaf in l:
                if printouts:
                    print('Deleting cached file:', cachefolder+'/'+l)
                os.remove(cachefolder+'/'+l)

def delete_checkpoint(name):
    if name in fglobals['checkpoints']:
        del fglobals['checkpoints'][name]

############################### Changes to several files at once ###############

def f_impose(fname2txt):
    # Creates or deletes files. Uses fsave, which ensures folders are created if need be.
    for k in fname2txt.keys():
        if fname2txt[k] is None:
            fdelete(fname2txt[k])
        else:
            fsave(k, fname2txt[k])

def revert_checkpoint(check_name):
    # Revert to a given checkpoint.
    fname2txt = fglobals['checkpoints'][check_name].copy() # The copy is important since it is modified inside the for loop!


#################################Debug safety and testing#######################

def _fileallow(fname):
    keeplist = debug_restrict_disk_modifications_to_these
    fname = termp_abs_path(fname)
    if keeplist is not None:
        if type(keeplist) is str:
            keeplist = [keeplist]
        keeplist = [termp_abs_path(kl) for kl in keeplist]
        allow = False
        for k in keeplist:
            if fname.startswith(k):
                allow = True
        return allow
    else:
        return True

def gaurded_delete(fname, allow_folders=False):
    # Deleting is dangerous.
    fname = termp_abs_path(fname)
    if not _fileallow(fname):
        raise Exception('debug_restrict_disk_modifications_to_these is set to: '+str(debug_restrict_disk_modifications_to_these).replace('\\\\','/')+' and disallows deleting this filename: '+fname)
    if os.path.isdir(fname) and not allow_folders:
        raise Exception('Attempt to delete folder (and whats inside) when allow_folders=False.')
    fdelete(fname)

def guarded_create(fname, is_folder):
    # Creating files isn't all that dangerous, but still can be annoying.
    # Skips files that already exist.
    fname = termp_abs_path(fname)
    if not _fileallow(fname):
        raise Exception('debug_restrict_disk_modifications_to_these is set to: '+str(debug_restrict_disk_modifications_to_these).replace('\\\\','/')+' and disallows creating this filename: '+fname)
    fcreate(fname, is_folder)
    return fname

def with_modifications(fname2contents, f, blanck_original_txts=False):
    # Allows temporary file modifications.
    # Runs f with the modified fname2contents.
    cname = '_tmp_with_modifications_checkpoint'; inw = '_inside_with_modifications'
    if fglobals.get(inw,None) is not None:
        raise Exception('Cannot nest with_modifications.')
    fglobals[inw] = True
    original_txts = fglobals['original_txts']
    if blanck_original_txts:
        fglobals['original_txts'] = {}

    save_checkpoint(cname)
    try:
        f_impose(fname2contents)
    except Exception as e:
        revert_checkpoint(cname)
        raise e

    exc = None
    try:
        f()
    except Exception as e:
        exc = e
    revert_checkpoint(cname)
    fglobals[inw] = False
    if blanck_original_txts:
        fglobals['original_txts'] = original_txts
    if exc is not None:
        print('Problem inside the function passed to with_modifications (see error below).')
        raise exc
