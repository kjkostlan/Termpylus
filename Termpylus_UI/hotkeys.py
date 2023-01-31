# Hotkeys are emacs-like. Change this sourcecode to change the hotkeys.
# See also: Termpylus_shell/hotcmds1.py
from . import evt_check

kys = {}
kys['grow_frame'] = 'M+='
kys['grow_frame_fast'] = 'SM+='
kys['shrink_frame'] = 'M+-'
kys['shrink_frame_fast'] = 'SM+-'
kys['grow_font'] = 'C+='
kys['shrink_font'] = 'C+-'
kys['grow_font_fast'] = 'CS+='
kys['shrink_font_fast'] = 'CS+-'
kys['focus_next'] = 'C+~'
kys['focus_prev'] = 'CS+~'
kys['run_cmd'] = 'S+Enter'
kys['clear_shell'] = 'C+k'