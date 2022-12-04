import asyncio, os, time, subprocess
#import asyncio.TaskGroup
#https://stackoverflow.com/questions/74664917/wrapping-a-shell-in-python-and-then-launching-subprocesses-in-said-shell

#https://docs.python.org/3/library/asyncio-task.html

'''
async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')

asyncio.run(run('ls /zzz'))

async def main():
    await asyncio.gather(
        run('ls /zzz'),
        run('sleep 1; echo "hello"'))

asyncio.run(main())
'''
# shlex.quote()
#https://stackoverflow.com/questions/68223828/how-to-use-asyncio-to-stream-process-data-between-3-subprocesses-using-pipes-a
#p = subprocess.Popen([proc], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#asyncio.create_subprocess_shell(proc,stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
#put_nowait
#p = asyncio.run()
outputs = []
#asyncio.gather([x,y,z])

p_holder = []
queue = asyncio.Queue()

def send_cmd(cmd):
    if len(cmd)>0:
        queue.put_nowait(cmd)

async def launch():
    shell_type = 'cmd' if os.name=='nt' else 'bash'
    p = await asyncio.create_subprocess_shell(
        shell_type,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    p_holder.append(p)

#https://stackoverflow.com/questions/64303607/python-asyncio-how-to-read-stdin-and-write-to-stdout
async def input_loop():
    while len(p_holder)==0:
        await asyncio.sleep(0.0625)
    while True:
        cmd = await queue.get() # Will block where when it is empty.
        p = p_holder[0]
        await p.stdin.write((cmd+'\n').encode())
        await p.stdin.flush()

async def output_loop():
    while len(p_holder)==0:
        await asyncio.sleep(0.0625)
    while True:
        p = p_holder[0]
        line = await p.stdout.readline()

async def error_loop():
    while len(p_holder)==0:
        await asyncio.sleep(0.0625)
    while True:
        p = p_holder[0]
        line = await p.stderr.readline()

async def main_async():
    #https://docs.python.org/3/library/asyncio-task.html
    await asyncio.gather(launch(), input_loop(), output_loop(), error_loop())

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main_async()) # Only use asyncio.run once!
send_cmd('echo foo')
print('Right after run call:',outputs)
time.sleep(0.125)
print('After run call:',outputs)
