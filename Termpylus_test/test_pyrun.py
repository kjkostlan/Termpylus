#Tests running python and updating changes to python.
import sys, os, imp, re
from Termpylus_core import projects
from Termpylus_shell import bashy_cmds, shellpython
from Termpylus_extern.fastatine import python_parse
from Termpylus_extern.waterworks import py_updater, file_io, paths, modules, var_watch, ppatch
from . import ttools

project_urls = ['https://github.com/Geraa50/arkanoid', 'https://github.com/ousttrue/pymeshio']
project_main_files = ['/main.py', '/bench.py']
outside_folder = paths.abs_path('../__softwaredump__/Termpylus/sample_projs', True)

def _fetch_sample_githubs(): # TODO: drepecated by code_in_a_box.py
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
    from . import changeme # adds to the sys.modules
    val0 = changeme.mathy_function(1000)
    py_updater.update_one_module(changeme.__name__)
    fname = './Termpylus_test/changeme.py'
    txt = file_io.fload(fname)
    if '1234' not in txt:
        txt0 = txt.replace('4321','1234')
        file_io.fsave(fname, txt0)
        raise Exception('Aborted test_py_update due to file save not bieng reverted. Try again.')
    eds0 = file_io.get_txt_edits()
    T0 = val0==1000+1234

    txt1 = txt.replace('1234','4321')
    if txt1==txt:
        raise Exception('The change failed.')
    file_io.fsave(fname, txt1)

    val1 = changeme.mathy_function(1000)
    eds1 = file_io.get_txt_edits()
    T1 = val1==1000+4321

    file_io.fsave(fname, txt) # revert.

    last_ed = eds1[-1]
    ed_len = (len(eds1)==len(eds0)+1)
    ed_test = last_ed[4] == '4321'
    #print('eds0 1:', eds0, eds1)

    return T0 and T1 and ed_len and ed_test

def test_eval():
    # Does eval (actually exec) work in all modules?
    def evl(mname, txt, deletevar=True):
        return deep_stack.exec_here(mname, txt, delete_new_vars=deletevar)

    out = True
    x = evl('Termpylus_test.test_pyrun', '_x_ = test_py_update')
    out = out and x['_x_'] is test_py_update
    y = evl('Termpylus_extern.waterworks.paths', '_y_ = is_path_absolute("./bar"); _z_ = 2')
    out = out and y['_y_'] is False
    out = out and '_y_' not in file_io.__dict__
    z = evl('Termpylus_core.todict', '_z_ = default_blockset({},[])')
    out = out and z['_z_'] == {}
    try:
        w = evl('Termpylus_test.test_pyrun', '_w_ = test_py_updyate')
        out = False
    except:
        pass
    w = evl('Termpylus_extern.waterworks.paths', '_w_ = is_path_absolute("./bar")', False)
    out = out and '_w_' in file_io.__dict__

    return out

def test_file_caches():
    py_updater.cache_module_code()
    mglob = py_updater.uglobals
    fnamemap = modules.module_fnames(True)
    t0 = len(mglob['filecontents'])>8
    t1 = set(mglob['filecontents'].keys())==set(mglob['filemodified'].keys())
    t2 = 'test_file_caches' in mglob['filecontents'][fnamemap['Termpylus_test.test_pyrun']]
    t3 = os.path.isfile(paths.abs_path(list(fnamemap.values())[4], True))
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
    paths.add_to_path(ark_fold)

    #https://linuxize.com/post/python-get-change-current-working-directory/
    #Change dir so that the file loads.
    dir0 = os.path.realpath('.')
    os.chdir(ark_fold)

    in_the_path = paths.abs_path(ark_fold, True) in sys.path
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
    projects.quit_all()
    out = [True]
    always_update = True
    bashy_mode = True # True and False should do the same thing.
    stream_printouts = True # False will save on how much stuff is dumped to console.
    out_status_printouts = True;
    # All these options should be True to ensure a thorough test, False for debugging:
    test_basic_run = True
    test_curveballs = True
    test_silent_file_edits = True
    test_external_file_edits = True
    test_collision_fn_mod = True
    test_queries = True

    def _outset(x, name):
        if out_status_printouts:
            print('test_run_arkanoid sub-test:',name, str(bool(x)), str(out[0])+'=>'+str(out and bool(x)))
        out[0] = out[0] and bool(x)

    ark_folder = outside_folder+'/arkanoid'
    txt = file_io.fload(ark_folder+'/brick_loader.py')
    if txt: # Reset an old change, in case we made it.
        txt1 = txt.replace('brick_images', 'brick_dict') # Reset.
        file_io.fsave(ark_folder+'/brick_loader.py', txt1, tries=12, retry_delay=1.0)

    def _silent_edit(forwards):
        pth = ark_folder+'/brick_loader.py'
        txt0 = file_io.fload(pth)
        if not txt0:
            raise Exception('txt is not existing.')
        ab = ['brick_dict', 'brick_images']
        if not forwards:
            ab = [ab[1], ab[0]]
        txt1 = txt0.replace(ab[0], ab[1])
        file_io.fsave(pth, txt1, tries=12, retry_delay=1.0)

    _silent_edit(False) # Undo edits made, if any.

    if test_external_file_edits: # Run this without loading the arkanoid program.
        _silent_edit(True) # The fsave should store edits.
        eds = file_io.get_txt_edits() # Shouldn't have any.
        test_ext_ed = "'dict', 'images'" in str(eds).replace('"',"'")
        _outset(test_ext_ed, 'test_ext_ed')

    mods = None # TODO? add mods.
    if always_update:
        print('DEBUG reset project every time next line below this.')
    if ark_proj[0] is None or always_update:
        print('About to download Arkanoid to: (NOTE: Changes to the repo may break this test)', ark_folder)
        if bashy_mode:
            shell_obj = shellpython.Shell()
            ark_proj[0] = bashy_cmds.python([project_urls[0], ark_folder+'/'+project_main_files[0]], shell_obj, printouts=stream_printouts)
            ark_proj[0].name = 'Arkanoid'
        else:
            ark_proj[0] = projects.PyProj(origin=project_urls[0], dest=folder, run_file=project_main_files[0],
                                          mod_run_file='default', refresh_dt=3600, printouts=stream_printouts)
            ark_proj[0].name = 'Arkanoid'
            ark_proj[0].launch()
    the_proj = ark_proj[0]
    #print("The project tubo is:", the_proj.tubo)

    ######################## SANDBOX ####################
    _do_sandbox = False
    if _do_sandbox:
        _silent_edit(True)

        # This causes the other process to diff the old files with the new files:
        projects.update_user_changed_modules_with_bcast(update_on_first_see=False)
        print('Sandbox mode, tests are in development...')
        _silent_edit(False)
        return False

    if test_basic_run:
        test_ez_run = projects.bcast_run('x = 2*3\nx') # Runing some code also? makes sure we are up-to-date.
        _outset(test_ez_run == [6], 'test_ez_run') # bcast_run returns a list, one element per project.
        test_ez_run1 = projects.bcast_run('y = 20*13\ny')
        _outset(test_ez_run1 == [20*13], 'test_ez_run1')
        xtxt = """Foo
bar
baz""".replace('\r\n','\n')
        xtxt = "'''"+xtxt+"'''"
        tq_code = f'''
x = {xtxt}.strip()
lines = x.split('\\n')
l = len(lines)
l'''
        test_tq_run = projects.bcast_run(tq_code)
        _outset(test_tq_run == [3], 'test_tq_run')

        a = projects.bcast_run('x = os.getcwd()\nx') # Folder-bound tests.
        _outset(type(a) is list and 'sample_projs/arkanoid' in a[0].replace('\\','/'), 'bcast getcwd')

        # Test a nested data structure:
        b = projects.bcast_run('''x = {"foo":"bar", "baz":[1,2,3]}\nx''')
        _outset(type(b[0]) is dict and 'baz' in b[0] and b[0]['baz'][0]==1, 'test nested run')

    if test_curveballs:
        unicody = 'z="ຝ"+"ᱝ"\nz'
        test_unicode_run = projects.bcast_run(unicody)
        _outset(test_unicode_run == [unicody[3]+unicody[7]], 'test unicode run')

        try:
            test_ez_run_err = projects.bcast_run('y = "foo"+1')
            _outset(False, 'bcast strincat error not thrown autofail.')
            out = False
        except Exception as e:
            _outset('can only concatenate str' in str(e), 'bcast strincat error correct message.')

    if test_silent_file_edits:
        projects.update_user_changed_modules_with_bcast(update_on_first_see=False)
        all_edits0 = projects.edits_with_bcast(True)
        _silent_edit(True)

        # This causes the other process to diff the old files with the new files:
        projects.update_user_changed_modules_with_bcast(update_on_first_see=False)

        print('Modified brick_loader.py, but can the program detect these mods?')
        all_edits = projects.edits_with_bcast(True)

        _outset(len(all_edits)>len(all_edits0) and 'brick_loader.py' in str(all_edits), 'Local silent edits.')
        _silent_edit(False)

    if test_collision_fn_mod:
        # This test has to be inspected visually.
        print_key = 'DETECT COLLISION CALLED' # TODO: somehow delay and search for this.
        code1 = f'''
_old_id_detect = id(detect_collision)
def detect_collision(dx, dy, ball, rect):
    # Modified to bounce the ball in a more interesting way.
    print({repr(print_key)})
    if dx > 0:
        delta_x = ball.right - rect.left
    else:
        delta_x = rect.right - ball.left
    if dy > 0:
        delta_y = ball.bottom - rect.top
    else:
        delta_y = rect.bottom - ball.top

    if abs(delta_x - delta_y) < 10:
        dx, dy = -dx, -dy
    elif delta_x > delta_y:
        dy = -dy
        dx = -0.5*dx # Modification.
    elif delta_y > delta_x:
        dx = -dx
        dy = -2.0*dy # Modification.
    return dx, dy
import sys
setattr(sys.modules[__name__], 'detect_collision', detect_collision) # Why doesn't def do anything!?
hex_ids = [hex(_old_id_detect), hex(id(detect_collision)), hex(id(getattr(sys.modules[__name__], 'detect_collision')))]
print('detect collision should now been changed:', hex_ids, 'module:', __name__)


'''
        code = f'''
from Termpylus_extern.waterworks import ppatch
code = """{code1}"""
modulename = '__main__'
var_name = "detect_collision"
v0 = ppatch.get_var(modulename, var_name)
ppatch.temp_exec(modulename, None, code)
v1 = ppatch.get_var(modulename, var_name)
#ppatch.set_var(modulename, var_name, None) # This destroys the function and causes the whole game to crash.
x=v0 is v1
print('Old and new var ids:', hex(id(v0)), hex(id(v1)))
x'''
        vars_not_changed = projects.bcast_run(code) # Should alter collision detection (can't easily be auto-tested, but can see the effect manually)
        print('ARE VARS CHANGED:', not vars_not_changed)

    if test_queries:
        # Test a source query: TODO: more of these queries.
        x = bashy_cmds.sfind(['-n', 'coll'], shell_obj=None)
        true_false = 'main__.Platform.collide_with_platform' in str(x) and len(x)<64 and len(x)>4
        _outset(true_false, 'test queries.')

    return out


def prepare_tests():
    ask_for_permiss = False
    if ask_for_permiss:
        x = input('These tests needs to download GitHub code to ' + outside_folder + ' y to preceed.')
        if x.strip() != 'y':
            return False
    _fetch_sample_githubs()
