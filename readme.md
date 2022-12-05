**Termpylus** is a python-based shell in which you write Python code. It has several user-friendly features that aren't found in a shell.

**You write Python:** Need a def? And if statement? A list comprehension? No need to be familiar with the bash flow-control. *anytime a variable is created you see it's printout*.

**Bash2python:** (**TODO**) As amazing as Python is, bash one-liners are *extremely* concise. Simple bash commands such as "cd path/to/dir" are converted into python commands. Allows setting python variables in the same line such as "x = ls". *This works even on windows* for the more common bash commands. There must be a Python library out there somewhere that implements "ls", "grep", "touch", etc...

**Multiline input:** Input multiline Python code all at once. Define multiple defs in a single command. Test that SSCCE with a single Ctrl+V!

**Visible history:** The command history is plainly shown and can be double-clicked on.

**Hotkeys for everything:** Since when does a shell require a mouse? Can be fully keyboard controlled (absent absentmindeness). **TODO:** document. Of course, this doesn't mean the mouse is useless...

**Default commands:** (**TODO**) Add startup.txt to this folder to load in (to the history) a list of default commands that you commonly use.

**Shell filtering:**(**MAJOR TODO**) Tired of sifting through a shell data-dump? Set up an automatic filter to screen out what you see.

**Save:** (**TODO**) Save your input, command history, and or output.