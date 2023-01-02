# Module loading and updating.
import sys, os

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


Many users will have experienced the issue of trying to use a submodule when only
importing the package that it is in:

$ python3
>>> import logging
>>> logging.config
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'module' object has no attribute 'config'

But it is less common knowledge that when a submodule is loaded anywhere it is
automatically added to the global namespace of the package:

$ echo "import logging.config" > weirdimport.py
$ python3
>>> import weirdimport
>>> import logging
>>> logging.config
<module 'logging.config' from '.../Python.framework/Versions/3.4/lib/python3.4/logging/config.py'>

'''

def module_dict():
    return sys.modules

def module_file(m):
    if type(m) is str:
        m = sys.modules[m]
    return os.path.abspath(m.__file__).replace('\\','/')
