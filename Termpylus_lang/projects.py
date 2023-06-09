# Handles projects.
import time
from Termpylus_core import file_io

class PyProj():
    def __init__(folder, github_URL=None, mods=None, git_refresh_time=3600):
        # mods is a list of string substituations.
        # A non-None github_URL will replace the contents of the folder!
        self.github_URL = github_URL
        self.folder = folder
        if mods is None:
            mods = []
        self.mods = mods
        self.git_refresh_time = git_refresh_time
        self.apply_mods()

    def apply_mods(self, assert=True):
        TODO

    def unapply_mods(self):
        # Call this fn when done with the project.
        TODO

    def last_git_time(self):
        TODO

    def git_update(self, ignore_refresh=False):
        # Updates the GitHub software, but only if ignore_refresh is True or git_refresh_time has elapsed.
        if self.github_URL is None:
            return None
        if ignore_refresh or time.time()-self.last_git_time()>self.git_refresh_time:

            TODO
