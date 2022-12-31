# Module loading and updating.
import sys
#list(pkgutil.iter_modules()) # even more full.
'''
The name shadowing trap
Another common trap, especially for beginners, is using a local module name that
shadows the name of a standard library or third party package or module that the
application relies on. One particularly surprising way to run afoul of this trap
is by using such a name for a script, as this then combines with the previous
“executing the main module twice” trap to cause trouble. For example, if
experimenting to learn more about Python’s socket module, you may be inclined to
call your experimental script socket.py. It turns out this is a really bad idea,
as using such a name means the Python interpreter can no longer find the real
socket module in the standard library, as the apparent socket module in the
current directory gets in the way.
'''
def module_dict():
    return sys.modules
