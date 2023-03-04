# Tests.
import sys, os, shutil
import tkinter.messagebox
from Termpylus_shell import shellpython, pybashlib
from Termpylus_UI import hotkeys
from . import ttools

def _alltrue(x):
    for xi in x:
        if not xi:
            return False
    return True

def _setup_tfiles():
    # Some files to test on. Shell starts in the dump folder.
    shell = shellpython.Shell()
    pybashlib.shell = shell

    shell.cur_dir = './softwaredump_'
    test_folder = os.path.abspath(shell.cur_dir)
    try:
        shutil.rmtree(test_folder)
    except FileNotFoundError:
        pass
    except PermissionError:
        print('Warning: Test_shell testbed is having a windoze moment.')
    file_io.debug_restrict_disk_modifications_to_these = [test_folder]

    subfiles = ['./foo.txt','./bar.txt']
    subfiles = subfiles+['./ocean/atlantic.txt', './ocean/pacific.txt']
    subfiles = subfiles+['./desert/mojave.txt', './desert/sahara.txt']
    subfiles = subfiles+['./mountain/sierra.txt', './mountain/applachia.txt', './mountain/kilimanjaro.txt']
    subfiles = subfiles+['./sky/cumulus.txt', './sky/nimbus.txt', './sky/airfoil.txt']

    for s in subfiles:
        fnamefull = pybashlib.guarded_create(s, '.txt' not in s)
        modified_fname = ''
        for si in s:
            modified_fname = modified_fname+si*3
        with open(fnamefull,'a') as f_obj:
            f_obj.writelines(modified_fname)

    return test_folder, subfiles, shell

################################################################################

def manual_tests():
    # We are using Tkinter directly and therefore lack an easy way to "abstract" the GUI to test it.
    # So here is a simple manual test.
    msg = '''
These following manual tests should pass:

R1. Run "x = 1"
    You should see x set to 1 in the printout. You can run with 'run_cmd' (emacs-style key cmds).
R2. Run "x = 2"
    You should see x set to 2 in the printout.
R3. Run "x = 2" again. You should see "command succeeded." but no var is changed so it will not report x.
S1. Hotkey test: 'focus_prev' and 'focus_next' should change focus (emacs-style key cmds).
S2. Hotkey test: 'shrink_font' and 'grow_font' should change the font size.
S3. Hotkey test: 'shrink_frame' and 'grow_frame' should change the focused window size.
S4. Hotkey test: 'clear_shell' to clear the output of the shell.
C1. Doubleclick on x = 1 and x=2 in the command history. The command should be put into the command window.
C2. The Python program should quit when closed, even if a cmd freezes.
'''
    for k in hotkeys.kys:
        msg = msg.replace( "'"+k+"'",hotkeys.kys[k])
    if "'" in msg:
        print(msg)
        raise Exception('Cant find all of the hotkeys for the manual instructions.')

    tkinter.messagebox.showinfo(title="Manual tests", message=msg)
    return True

def test_ls():
    #Wildcard matches.
    # Ls exmaples fropm cygwin:
    # ls => Just makes the ls.
    # ls . => same as ls.
    # ls main* => matches ./main.py
    # ls ../Termpylus/main* => matches ./main.py
    # ls ../Term* => Matches ls .
    # ls -r not recursive. But it should so we will have it work.
    # ls ../../Co*/Term. This works.
    test_folder, subfiles, shell = _setup_tfiles()
    tests = []

    x0 = pybashlib.ls('.')
    x1 = pybashlib.ls('-s','.')
    x2 = pybashlib.ls('-l','.')
    tests.append(len(x2)>len(x1))
    tests.append(len(x1)>len(x0))

    r1 = pybashlib.ls('-r','.')

    tests.append(len(x0.split(' '))*1.5+2<len(r1.split(' ')))

    r2 = pybashlib.ls('mount*') # Goes one level deeper for bash and us.
    tests.append('cumulus' not in str(r2) and 'kilimanjaro' in str(r2))
    r3 = pybashlib.ls('fo*')
    tests.append('foo.txt' in r3 and 'bar.txt' not in r3)

    return ttools.alltrue(tests)

def test_cd():
    test_folder, subfiles, shell = _setup_tfiles()

    l0 = pybashlib.ls('.')
    cur_dir0 = shell.cur_dir
    cd01 = pybashlib.cd('mountain')
    l1 = pybashlib.ls('.')
    cur_dir1 = shell.cur_dir
    cd12 = pybashlib.cd('..')
    l2 = pybashlib.ls('.')
    cur_dir2 = shell.cur_dir

    tests = []
    tests.append(str(l0)==str(l2))
    tests.append('applachia.txt' in str(l1) and 'sahara.txt' not in str(l1))
    tests.append('mountain' in cur_dir1 and 'mountain' not in cur_dir0)

    return ttools.alltrue(tests)

def test_grep():
    # TODO: more comprehensive test.
    x = pybashlib.grep('-r','f', '.')
    tests = []
    tests.append(len(x)>1 and len(x)<8)

    x1 = pybashlib.grep('f', '.')
    tests.append(len(x)>1 and len(x)<8)

    tests.append(len(x1)==1)

    print("tests are:", tests)

    try:
        x2 = pybashlib.grep('f', 'file_no_exist')
        tests.append(False)
    except: #Grep in bash throws errors if files don't exist.
        tests.append(True)

    x3 = pybashlib.grep('string_not_found', '.')

    tests.append(len(x3)==0)
    return _alltrue(tests)

def test_others():
    # Other bash fns.
    return False

def run_tests():
    return ttools.run_tests(__name__)
