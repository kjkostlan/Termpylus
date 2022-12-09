# Tests.
import tkinter.messagebox

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

def text_py2_bash():
    # Python to bash.
    txts = []
    unchanged = []
    unchanged.append('x = 1')
    unchanged.append('x = 1\n y=2\nz=3')

    pairs = []
    pairs.append(['ls -a','_ans = ls(["-a"])'])
    pairs.append(['x = ls -a','x = ls(["-a"])'])
    pairs.append(['blender','run("blender",[])'])
    pairs.append(['blender -foo','run("blender",["foo"])'])
    pairs.append(['blender "foo"','run("blender",["foo"])'])

    for x in unchanged:
        if x != sh.autocorrect(x):
            raise Exception('This should not be bash-i-fied, but it was:' + str(x) + str(sh.autocorrect(x)))

    for p in pairs:
        p0 = p[0]; p1 = p[1]; p1g = sh.autocorrect(p[0])
        if p1g != p1:
            raise Exception('Bashification incorrect:'+'X0:'+p0+'Gold:'+p1+' Green:'+p1g)

    return True

def test_matching():
    #Wildcard matches.
    return False

def test_cd():
    return False

def test_grep():
    return False

def test_ls():
    return False

def test_others():
    # Other bash scripts.
    return False

def run_tests():
    d = sys.modules[__name__].__dict__
    vars = list(d.keys())
    vars.sort()
    failed_tests = []
    for v in vars:
        v_obj = d[v]
        x = var_obj()
        if not x:
            failed_tests.append(v)
    if len(failed_tests)>0:
        raise Exception('Test failed:'+str(v))
    return True

if __name__ == __main__:
    run_tests() # python test.py
