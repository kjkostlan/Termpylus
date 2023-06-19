# Handles projects.
import sys, os, time, shutil
from Termpylus_shell import bashy_cmds, shellpython
from Termpylus_extern.waterworks import file_io

class PyProj():
    def __init__(self, origin, dest, run_file, mods=None, refresh_dt=3600):
        # mods is a list of string substituations.
        # A non-None github_URL will replace the contents of the folder!
        self.origin = origin # Folder or URL.
        self.dest = dest # Must be a folder.
        self.run_file = run_file
        self.refresh_dt = refresh_dt
        self.last_refresh_time = -1e100

        self.independ = 2 # 0 = run in same thread, 1 = different thread same process, 2 = different process.

        if mods is None:
            mods = {}
        self.mods = mods
        self.download()
        self.unmods = {}
        for m in self.mods.keys():
            if os.path.exists(self.dest+'/'+self.mods[m]):
                self.unmods[m] = file_io.fload(fname)
            else:
                self.unmods[m] = None # A new file which will need to be deleted.

    def _apply_mods_core(self, the_mods):
        for k in the_mods.keys():
            m = the_mods[k]
            fname = self.folder+'/'+k, mods[k]
            if callable(m):
                txt = m(file_io.fload(fname))
                file_io.fsave(fname, txt)
            elif not m:
                file_io.fdelete(fname)
            elif type(m) is str or type(m) is bytes:
                file_io.fsave(fname, m)
            else:
                raise Exception(f'The mod must be False, a callable, or a string; not a {type(m)}')

    def apply_mods(self):
        # Any modes that need to be changed.
        self._apply_mods_core(self.mods)

    def unapply_mods(self):
        # Call this fn when done with the project.
        self._apply_mods_core(self.unmods)

    def download(self, force_update=False):
        # Updates the GitHub software, but only if ignore_refresh is True or git_refresh_time has elapsed.
        if not force_update and time.time()-self.last_refresh_time < self.refresh_dt:
            return False
        if '//github.com' in self.origin or '//www.github.com' in self.origin:
            print('Fetching from GitHub')
            qwrap = lambda txt: '"'+txt+'"'
            file_io.fdelete(self.dest)
            file_io.fcreate(self.dest, True)
            cmd = ' '.join(['git','clone',qwrap(self.origin), qwrap(self.dest)])
            os.system(cmd) #i.e. git clone https://github.com/the_use/the_repo the_folder. os.system will wait for the cmd to finish.
            print('Git Clones saved into this folder:', self.dest)
        elif self.origin.startswith('http'):
            raise Exception(f'TODO: support other websites besides GitHub; in this case {self.origin}')
        elif self.origin.startswith('ftp'):
            raise Exception('FTP requests not planned to be supported.')
        else:
            folder = file_io.abs_path(self.origin, True)
            dest_folder = file_io.abs_path(self.dest, True)
            if folder != dest_folder:
                if not os.path.exists(folder):
                    raise Exception(f'The origin is a folder on a local machine: {folder} but that folder does not exist.')
                file_io.fdelete(self.dest)
                shutil.copytree(folder, self.dest)
        self.last_refresh_time = time.time()
        self.apply_mods()
        return True

    def run(self):
        shell_obj = shellpython.Shell()
        fname = self.dest+'/'+self.run_file
        if self.dest not in sys.path:
            sys.path.append(self.dest)
        if self.independ == 0:
            return bashy_cmds.python([sfname], shell_obj)
        elif self.independ == 1:
            return bashy_cmds.python([fname, '--th'], shell_obj)
        elif self.independ == 2:
            return bashy_cmds.python([fname, '--pr'], shell_obj)
        elif self.independ == 3:
            raise Exception('TODO: Cloud run option.')
