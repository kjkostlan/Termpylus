# More hot commands.
# Functions go here for ease of acess and are avaialbe w/o import.

def splat_here(modulename):
    kvs = cmds1()
    module = sys.modules[modulename]
    for k in kvs.keys():
        module.__dict__[k] = kvs[k]
