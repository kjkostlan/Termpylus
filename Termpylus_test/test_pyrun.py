#Tests running python and updating changes to python.
import sys, os, imp, re
from Termpylus_core import projects
from Termpylus_shell import bashy_cmds, shellpython
from Termpylus_extern.fastatine import python_parse
from Termpylus_extern.waterworks import py_updater, file_io, modules, var_watch, ppatch
from . import ttools

project_urls = ['https://github.com/Geraa50/arkanoid', 'https://github.com/ousttrue/pymeshio']
project_main_files = ['/main.py', '/bench.py']
outside_folder = file_io.abs_path('../__softwaredump__/Termpylus/sample_projs', True)

def _fetch_sample_githubs():
    # Fetch sample githubs into an external softwaredump folder.
    print('Fetching GIT samples into', outside_folder)
    ask_for_permiss = False
    if ask_for_permiss:
        x = input('These tests needs to download GitHub code to ' + outside_folder + ' y to preceed.')
        if x.strip() != 'y':
            return False
    qwrap = lambda txt: '"'+txt+'"'
    file_io.power_delete(outside_folder)
    file_io.fcreate(outside_folder, True)
    for i in range(len(project_urls)):
        url = project_urls[i]
        local_folder = outside_folder+'/'+url.split('/')[-1]
        cmd = ' '.join(['git','clone',qwrap(url), qwrap(local_folder)])
        os.system(cmd) #i.e. git clone https://github.com/the_use/the_repo the_folder.
    print('Git Clones saved into this folder:', outside_folder)

def test_py_update():
    # Tests making changes to the source code: do we update the code properly and do we record the edits?
    if py_updater.record_txt_update_fn is None:
        raise Exception('Linking the record_txt_update_fn to the py_updater module was not done.')

    from . import changeme # adds to the sys.modules
    val0 = changeme.mathy_function(1000)
    py_updater.update_one_module(changeme.__name__)
    #print('Val00 is:', val0)
    fname = './Termpylus_test/changeme.py'
    #x0 = modules.update_all_modules(use_date=False, update_on_first_see=False)
    txt = file_io.fload(fname)
    if '1234' not in txt:
        txt0 = txt.replace('4321','1234')
        file_io.fsave(fname, txt0)
        raise Exception('Aborted test_py_update due to file save not bieng reverted. Try again.')
    eds0 = var_watch.get_txt_edits()
    T0 = val0==1000+1234

    txt1 = txt.replace('1234','4321')
    if txt1==txt:
        raise Exception('The change failed.')
    py_updater.save_py_file(fname, txt1, assert_py_module=True)

    val1 = changeme.mathy_function(1000)
    eds1 = var_watch.get_txt_edits()
    T1 = val1==1000+4321
    py_updater.save_py_file(fname, txt, assert_py_module=True) # revert.

    last_ed = eds1[-1]
    ed_len = (len(eds1)==len(eds0)+1)
    ed_test = last_ed[4] == '1234' and last_ed[5] == '4321'

    return T0 and T1 and ed_len and ed_test

def test_eval():
    # Does eval (actually exec) work in all modules?
    def evl(mname, txt, deletevar=True):
        return ppatch.eval_here(mname, txt, delete_new_vars=deletevar)

    out = True
    x = evl('Termpylus_test.test_pyrun', '_x_ = test_py_update')
    out = out and x['_x_'] is test_py_update
    y = evl('Termpylus_extern.waterworks.file_io', '_y_ = is_path_absolute("./bar"); _z_ = 2')
    out = out and y['_y_'] is False
    out = out and '_y_' not in file_io.__dict__
    z = evl('Termpylus_core.todict', '_z_ = default_blockset({},[])')
    out = out and z['_z_'] == {}
    try:
        w = evl('Termpylus_test.test_pyrun', '_w_ = test_py_updyate')
        out = False
    except:
        pass
    w = evl('Termpylus_extern.waterworks.file_io', '_w_ = is_path_absolute("./bar")', False)
    out = out and '_w_' in file_io.__dict__

    return out

def test_file_caches():
    py_updater.startup_cache_sources()
    mglob = py_updater.uglobals
    fnamemap = modules.module_fnames(True)
    t0 = len(mglob['filecontents'])>8
    t1 = set(mglob['filecontents'].keys())==set(mglob['filemodified'].keys())
    t2 = 'test_file_caches' in mglob['filecontents'][fnamemap['Termpylus_test.test_pyrun']]
    t3 = os.path.isfile(file_io.abs_path(list(fnamemap.values())[4], True))
    return t0 and t1 and t2 and t3

def test_dynamic_add_fn():
    # Can we add a function that uses a module's variables?
    out = True
    from . import test_varmodtrack
    modul = test_varmodtrack
    def foo(bar):
        if bar>0:
            x = test_var_get
            return type(x)
        else:
            return modul
    modul.foo = foo

    try: # This wont work.
        ty = modul.foo(1)
        out = False
    except Exception as e:
        if "name 'test_var_get' is not defined" not in str(e):
            raise e
    modul = modul.foo(0) # But variables HERE are accessable; def evaluates into this module.

    bar_txt = '''
def bar(foo):
    x = test_var_get
    return [x,2,3]
'''

    exec(bar_txt, modul.__dict__)
    out = out and modul.bar(1)[0] is modul.test_var_get

    return out

def test_main_extract():
    # Tests whether we can extract the if __name__ is __main__ part.
    # ALSO tests loadiing a module.
    out = True
    piefile = project_main_files[0]; modname = piefile.replace('.py','').replace('/','')
    leaf_samples = [url.split('/')[-1] for url in project_urls]
    sample_github_folders = [outside_folder+'/'+leaf_sample for leaf_sample in leaf_samples]

    # TWO ways to import:
    import importlib
    ark_fold = outside_folder+'/'+leaf_samples[0]
    modules.add_to_path(ark_fold)

    #https://linuxize.com/post/python-get-change-current-working-directory/
    #Change dir so that the file loads.
    dir0 = os.path.realpath('.')
    os.chdir(ark_fold)

    in_the_path = file_io.abs_path(ark_fold, True) in sys.path
    out = out and in_the_path
    print('Arkanoid folder:', ark_fold, 'Added to the system path:', in_the_path)

    try:
        importlib.import_module('main')
    except Exception as e:
        if 'cannot convert without pygame.display initialized' not in str(e):
            raise e
        else:
            print('Annoying pygame error...')
    print('Main module:', str(sys.modules.get('main',None)))

    modules.module_fnames(True)
    if_name_main_blocks = python_parse.get_main_blocks(file_io.fload(modules.module_file(modname)))

    out = out and len(if_name_main_blocks) == 2
    out = out and "pygame.display.set_caption('arkanoid')" in if_name_main_blocks[0]
    out = out and "bricks, platform, ball, bricks_quantity = game_field_init()" in if_name_main_blocks[1]
    os.chdir(dir0)
    return out

try:
    ark_proj
except:
    ark_proj = [None]

def test_run_arkanoid():
    # BIG TEST!
    # Interacts with a process.
    always_update = True
    bashy_mode = True # True and False should do the same thing.
    if always_update:
        print('DEBUG reset project every time next line below this.')

    folder = outside_folder+'/arkanoid'
    mods = None # TODO: add mods.
    if ark_proj[0] is None or always_update:
        projects.quit_all()
        print('About to download Arkanoid to folder:', folder)
        if bashy_mode:
            shell_obj = shellpython.Shell()
            ark_proj[0] = bashy_cmds.python([project_urls[0], folder+'/'+project_main_files[0]], shell_obj)
        else:
            ark_proj[0] = projects.PyProj(origin=project_urls[0], dest=folder, run_file=project_main_files[0],
                                          mod_run_file='default', refresh_dt=3600, printouts=True)
            ark_proj[0].launch()
    the_proj = ark_proj[0]
    print("The project tubo is:", the_proj.tubo)

    # Test sending a simple command which returns a small nested structure:
    a = projects.bcast_run('x = 1+3\nx')
    #b = projects.bcast_run('print(8*4)') # TODO: uncomment (debug)

    print('Stuff:', a, b)
    return False
    TODO

    # Test a source search with the Arkanoid in addition to Termpylus:
    TODO

    # Test edits (there should be no edits, but still not much of a test):
    projects.update_user_changed_modules_with_bcast()
    TODO

    # Test Pythonverse, searching by a particular path; maybe this test will not work well?
    TODO

    # The bashy cmds version
    TODO
    #bashy_cmds.pwatch(bashy_args, shell_obj=None) # Bcasts the var_watch command.
    #bashy_cmds.edits(bashy_args, shell_obj=None)
    #bashy_cmds.sfind(bashy_args, shell_obj=None)
    #bashy_cmds.pfind(bashy_args, shell_obj=None)

    #projects.bcast_run(code_txt)
    #projects.var_watch_with_bcast(fn_name, args)
    #projects.edits_with_bcast()
    #projects.generic_pythonverse_find_with_bcast(bashy_args)
    #projects.generic_source_find_with_bcast(bashy_args)

    #print('Sleep 3 seconds then blit TODO dedebug:')
    #import time
    #time.sleep(3)
    #print('Blitted tubo:', the_proj.blit())
    #print('Len of blitted tubo:', len(the_proj.blit()))

def prepare_tests():
    ask_for_permiss = False
    if ask_for_permiss:
        x = input('These tests needs to download GitHub code to ' + outside_folder + ' y to preceed.')
        if x.strip() != 'y':
            return False
    _fetch_sample_githubs()
