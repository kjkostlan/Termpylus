# Tests.
import sys, os, shutil
import tkinter.messagebox
from Termpylus_shell import shellpython, pybashlib

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
        print('Warning: This testbed is having a windoze moment.')
    pybashlib.debug_only_these_folders = [test_folder]

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

1. Run "x = 1"
    You should see x set to 1 in the printout.
2. Run "x = 2"
    You should see x set to 2 in the printout.
3. Run "x = 2" again. You should see "command succeeded." but no var is changed so it won't report x.
3. Hotkey test: C+` and C+S+` should change focus.
4. Hotkey test: C+- and C+= should change the font size.
5. Hotkey test: M+- and M+= should change the focused window size.
6. Doubleclick on x = 1 and x=2 in the command history. The command should be put into the command window.
7. Same as (4) but with keyboard and enter.
8. The Python program should quit when closed, unless there is a running shell command.
'''
    tkinter.messagebox.showinfo(title="Manual tests", message=msg)
    return True

def test_py2_bash():
    # Python to bash.
    txts = []
    unchanged = []
    unchanged.append('x = 1')
    unchanged.append('x = 1\n y=2\nz=3')

    pairs = []
    pairs.append(['ls -a','_ans = ls(["-a"])'])
    pairs.append(['x = ls -a','x = ls(["-a"])'])
    pairs.append(['blender','_ans, _err = run("blender", [])'])
    pairs.append(['blender -foo','_ans, _err = run("blender", ["-foo"])'])
    pairs.append(['blender "foo"','_ans, _err = run("blender", ["foo"])'])
    pairs.append(['x = blender "foo"','x, _err = run("blender", ["foo"])'])

    sh = shellpython.Shell()

    for x in unchanged:
        if x.strip() != sh.autocorrect(x).strip():
            raise Exception('This should not be bash-i-fied, but it was:' + str(x) + str(sh.autocorrect(x)))

    for p in pairs:
        p0 = p[0]; p1 = p[1]; p1g = sh.autocorrect(p[0])
        if p1g != p1:
            raise Exception('Bashification incorrect, '+'X0: '+p0+' Gold: '+p1+' Green: '+p1g)

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

    x0 = pybashlib.ls(['.'])
    x1 = pybashlib.ls(['-s','.'])
    x2 = pybashlib.ls(['-l','.'])
    tests.append(len(x2)>len(x1))
    tests.append(len(x1)>len(x0))

    r1 = pybashlib.ls(['-r','.'])

    tests.append(len(x0.split(' '))*1.5+2<len(r1.split(' ')))

    r2 = pybashlib.ls(['mount*']) # Goes one level deeper for bash and us.
    tests.append('cumulus' not in str(r2) and 'kilimanjaro' in str(r2))
    r3 = pybashlib.ls(['fo*'])
    tests.append('foo.txt' in r3 and 'bar.txt' not in r3)

    #print('r3:',r3)

    #print('Tests:', tests)

    #print('Ls test:', pybashlib.ls(['-r','.']))
    #print('Ls test:', pybashlib.ls(['.']))
    #print('Ls test:', pybashlib.ls(['-s','.']))
    #print('Ls test:', pybashlib.ls(['-l','.']))
    return _alltrue(tests)

def test_cd():
    test_folder, subfiles, shell = _setup_tfiles()

    l0 = pybashlib.ls(['.'])
    cur_dir0 = shell.cur_dir
    cd01 = pybashlib.cd(['mountain'])
    l1 = pybashlib.ls(['.'])
    cur_dir1 = shell.cur_dir
    cd12 = pybashlib.cd(['..'])
    l2 = pybashlib.ls(['.'])
    cur_dir2 = shell.cur_dir

    tests = []
    tests.append(str(l0)==str(l2))
    tests.append('applachia.txt' in str(l1) and 'sahara.txt' not in str(l1))
    tests.append('mountain' in cur_dir1 and 'mountain' not in cur_dir0)

    return _alltrue(tests)

def test_grep():
    # TODO: more comprehensive test.
    x = pybashlib.grep(['-r','f', '.'])
    tests = []
    tests.append(len(x)>1 and len(x)<8)

    x1 = pybashlib.grep(['f', '.'])
    tests.append(len(x)>1 and len(x)<8)

    tests.append(len(x1)==1)
    #_alltrue(tests)
    try:
        x2 = pybashlib.grep(['f', 'file_no_exist'])
        tests.append(False)
    except: #Grep in bash throws errors if files don't exist.
        tests.append(True)

    x3 = pybashlib.grep(['string_not_found', '.'])

    tests.append(len(x3)==0)
    return _alltrue(tests)

def test_others():
    # Other bash fns.
    return False

def run_tests():
    d = sys.modules[__name__].__dict__
    vars = list(d.keys())
    vars.sort()
    failed_tests = []
    for v in vars:
        if '__' in v:
            continue
        if 'run_tests' in v:
            continue
        if 'test' not in v:
            continue
        v_obj = d[v]
        if type(v_obj) is not type(sys):
            x = v_obj()
            if not x:
                failed_tests.append(v)
    if len(failed_tests)>0:
        raise Exception('Tests failed: '+str(failed_tests))
    return True

if __name__ == "__main__":
    run_tests()
