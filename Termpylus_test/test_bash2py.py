# Tests converting lines of Bash to Python.
# The conversion is vary far from a comprehensive transpiler.
# Instead, it is designed to transform with simple commands such as:
#    "echo foo bar baz" => ans = bashy_cmds.echo('foo', 'bar', 'baz')
# One tricky part is that an input may *mix* Python and Bash lines.
from Termpylus_shell import bash2py

def test_tier0():
    # Simple tests.
    f = bash2py.maybe_bash2py_console_input
    ck = lambda a,b: a.replace('"',"'").strip()==b.replace('"',"'").strip()
    pairs = []
    pairs.append(['echo foo', 'ans = echo("foo")'])

    tripq_txt =    """echo bar baz

'''
ls -a
'''""".strip()
    tripq_txt1 = tripq_txt.replace('echo bar baz', 'ans = echo("bar", "baz")')

    pairs.append([tripq_txt, tripq_txt1])

    tresults = []
    for p in pairs:
        gold = p[1]; green = f(p[0])
        tresults.append(ck(gold, green))

    return tresults

def test_tier1():
    # More involved tests.
    # TODO: We should have most/all of these tested (some in tier0, some in tier1):
    #bashy_heuristic(line)
    #lines_vs_python(code)
    #blob(pline)
    #is_line_bash(pline_py, assert_decision=True)
    #strict_mode = False
    #maybe_bash2py_console_input(txt)
    #add_varset(ast_obj)
    #_ast_core(ptxts)
    #ast_bash(txt)
    return False
