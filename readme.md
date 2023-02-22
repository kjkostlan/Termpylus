##Maturity: Alpha. Development: Very active


**Termpylus** is a python-based shell in which you write Python code. It has several user-friendly features that aren't found in a shell.

**You write Python:** Need a def? And if statement? A list comprehension? No need to be familiar with the bash flow-control. Printouts are given when variables are created or modified.

**Multiline input:** Input multiline Python code all at once. Define multiple defs in a single command. Test that SSCCE with a single Ctrl+V.

**Bash2python:** As amazing as Python is, bash one-liners are *extremely* concise. Simple bash commands such as "cd path/to/dir" are converted into python commands (unfortunately there is a general lacking of bash clones in python so these mostly had to be written manually). Also, "x = ls -a" will set the variable x to the output of "ls -a". TODO: add more bash commands.

**Pythonic searching:** Call "python path/to/project/main.py" to launch a project. Search the code based on the function name, it's source code, how "new" it's source code is, it's use count, or even it's inputs and outputs. The latter will require adding *loggers* to the project's functions. Note: this section is very much under active development and hasn't yet been extensively tested.

**Visible history:** The command history is plainly shown and can be double-clicked on. Repeated commands are collapsed and shown in chronological order of last time ran. Outputs are color-coded so that is clear where one output ended and the next began.

**Hotkeys for everything:** Since when does a shell require a mouse? Can be fully keyboard controlled (this includes resizing the windows).

# TODO features:

**Startup:** Add a startup.py to this folder to load in (to the history), which would work the same way as MATLABs startup.m.

**Shell filtering:** Tired of sifting through a shell data-dump? Set up an automatic filter to screen out what you see.

**Save:** (**TODO**) Save your input, command history, and or output.
