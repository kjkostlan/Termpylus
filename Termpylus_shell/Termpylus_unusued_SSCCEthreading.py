# Windows async: start python SSCCEfail.py
# Linux async: python SSCCEfail.py &
import subprocess, threading, os, time

proc = 'cmd' if os.name=='nt' else 'bash'

messages = []

p = subprocess.Popen([proc], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#py_rw = os.pipe()
#p = subprocess.Popen([proc], shell=True, stdin=py_rw[1], stdout=py_rw[0], stderr=subprocess.PIPE)
exit_loops = False
def read_stdout():
    while not exit_loops:
        msg = p.stdout.readline()
        messages.append(msg.decode())
def read_stderr():
    while not exit_loops:
        msg = p.stderr.readline()
        messages.append(msg.decode())
threading.Thread(target=read_stdout).start()
threading.Thread(target=read_stderr).start()

# This works:
p.stdin.write('echo foo\n'.encode())
p.stdin.flush()
time.sleep(0.125)
print('Messages echo test:', messages)
del messages[:]

# This fails:
p.stdin.write('python\n'.encode())
p.stdin.flush()
p.stdin.write('x = 123\n'.encode())
p.stdin.flush()
p.stdin.write('print("x is:",x)\n'.encode())
p.stdin.flush()
p.stdin.write('y = nonexistant_var\n'.encode())
p.stdin.flush()
p.stdin.write('quit()\n'.encode())
p.stdin.flush()
time.sleep(1.5)
print('Messages python test:', messages)

# This generates a python error b/c quit() didn't actually quit:
p.stdin.write('echo bar\n'.encode())
p.stdin.flush()
time.sleep(0.125)
print('Messages echo post-python test:', messages)