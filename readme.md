# Termpylus

**Termpylus** is a Python-powered shell which aims to replace Bash as an interactive shell. The shell also provides Python features for debugging python projects.

Reclur inspired this project. This project is a prelude to TuringCreate: it's features will be used to help develop it.

## Shell features

**You write Python:** Need a def? And if statement? A list comprehension? No need to be familiar with the bash flow-control. Printouts are given when variables are created or modified.

**Multiline input:** Input multiline Python code all at once. Define multiple defs in a single command. Test that SSCCE with a single Ctrl+V.

**Bash2python:** As amazing as Python is, bash one-liners are *extremely* concise. Simple bash commands such as "cd path/to/dir" are converted into python commands (unfortunately there is a general lacking of bash clones in python so these mostly had to be written manually).

**Visible history:** The command history is plainly shown and can be double-clicked on. Repeated commands are collapsed and shown in chronological order of last time ran. Outputs are color-coded so that is clear where one output ended and the next began.

**Hotkeys for everything:** Since when does a shell require a mouse? Can be fully keyboard controlled (this includes resizing the windows).

## Python features

**Launching a project:** The python command launches a Python project, in the same thread, a separate thread, or a separate process. Any modules loaded by the project's main file (directly or indirectly) are available to work with.

**Auto-update:** The shell looks to any changed python file among the loaded modules and updates it before running the command.

**Variable watching:** Log inputs or outputs of various function in any of the loaded python modules. Useful for debugging.

**Code searching:** Search your codebase based on watched variable logs, the function name, the function source code, or other features. Or a weighted combination of all of these (encoded in a simple bash like syntax).

## Planned features:

**Startup:** Add a startup.py to this folder to load in (to the history), which would work the same way as MATLABs startup.m.

**More shell commands:** There isn't a good library as far as I know so many Bash commands have to be implemented manually. Fortunately they are often simple.

**Save:** Save your input, command history, and or output.

# Development status
This project is in alpha and under active development.
