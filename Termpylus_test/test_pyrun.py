#Tests running python and updating changes to python.
import sys, os, imp
from Termpylus_core import var_watch, updater, file_io
from Termpylus_shell import bashy_cmds, shellpython
from Termpylus_lang import ppatch, modules
from . import ttools

def test_py_import0():
    # Optional extra test. Returns True unless there is a simplypyimport test folder
    # outside of our main directory for which it will try importing it.
    # If this test fails (with the right folder & contents) opening a project will fail.
    kys0 = list(sys.modules.keys())
    folder = os.path.dirname(os.path.realpath(__file__)).replace('\\','/')
    folder = folder.replace('Termpylus','')+'/../simplypyimport/'
    if not os.path.exists(folder):
        print('Warning: external directory for testing does not exist.')
        return True

    shell_obj = shellpython.Shell()
    mdle = bashy_cmds.python([folder+"smain.py"], shell_obj)
    return True

def test_py_update():
    # Tests making changes to the source code.
    from . import changeme # adds to the sys.modules
    val0 = changeme.mathy_function(1000)
    updater.update_one_module(changeme.__name__)
    #print('Val00 is:', val0)
    fname = './Termpylus_test/changeme.py'
    #x0 = modules.update_all_modules(use_date=False, update_on_first_see=False)
    txt = file_io.contents(fname)
    if '1234' not in txt:
        txt0 = txt.replace('4321','1234')
        file_io.fsave(fname, txt0)
        raise Exception('Aborted test_py_update due to file save not bieng reverted. Try again.')
    eds0 = var_watch.get_txt_edits()
    T0 = val0==1000+1234

    txt1 = txt.replace('1234','4321')
    if txt1==txt:
        raise Exception('The change failed.')
    updater.save_py_file(fname, txt1, assert_py_module=True)

    val1 = changeme.mathy_function(1000)
    eds1 = var_watch.get_txt_edits()
    T1 = val1==1000+4321
    updater.save_py_file(fname, txt, assert_py_module=True) # revert.

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
    y = evl('Termpylus_core.file_io', '_y_ = is_path_absolute("./bar"); _z_ = 2')
    out = out and y['_y_'] is False
    out = out and '_y_' not in file_io.__dict__
    z = evl('Termpylus_core.todict', '_z_ = default_blockset({},[])')
    out = out and z['_z_'] == {}
    try:
        w = evl('Termpylus_test.test_pyrun', '_w_ = test_py_updyate')
        out = False
    except:
        pass
    w = evl('Termpylus_core.file_io', '_w_ = is_path_absolute("./bar")', False)
    out = out and '_w_' in file_io.__dict__

    return out

def test_file_caches():
    updater.startup_cache_sources()
    mglob = updater.uglobals
    fnamemap = modules.module_fnames(True)
    t0 = len(mglob['filecontents'])>8
    t1 = set(mglob['filecontents'].keys())==set(mglob['filemodified'].keys())
    t2 = 'test_file_caches' in mglob['filecontents'][fnamemap['Termpylus_test.test_pyrun']]
    t3 = os.path.isfile(list(fnamemap.values())[4])
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


def test_python_openproject():
    # BIG TEST!
    # Our "python" command tries to launch a python program.
    # A github project is downloaded into an alternate folder.

    project_urls = ['https://github.com/Geraa50/arkanoid', 'https://github.com/ousttrue/pymeshio']
    project_main_files = ['/main.py', '/bench.py']
    outside_folder = file_io.absolute_path('../__softwaredump__')
    print('Git Clones into this folder:', outside_folder)
    ask_for_permiss = False
    if ask_for_permiss:
        x = input('This test needs to download GitHub code to ' + outside_folder + ' y to preceed.')
        if x.strip() != 'y':
            return False
    qwrap = lambda txt: '"'+txt+'"'
    file_io.fdelete(outside_folder)
    file_io.fcreate(outside_folder, True)
    shell_obj = shellpython.Shell()
    for i in range(len(project_urls)):
        if i==1:
            return False
        url = project_urls[i]
        local_folder = outside_folder+'/'+url.split('/')[-1]
        main_py_file = file_io.absolute_path(local_folder+'/'+project_main_files[i])
        main_py_folder = os.path.dirname(main_py_file) # TODO: use this.
        cmd = ' '.join(['git','clone',qwrap(url),qwrap(local_folder)])
        #print('Cmd is:', cmd); return False
        os.system(cmd) #i.e. git clone https://github.com/the_use/the_repo the_folder.
        # -th = Thread, -pr = process. Neither = Not applicable.
        x = bashy_cmds.python([main_py_folder, '--th'], shell_obj)
    return False # TODO.

def run_tests():
    return ttools.run_tests(__name__)
