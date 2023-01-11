# Usage tracking. But instead of bieng for the benefit of huge cooperations,
# it is for the end users.
import sys, time, difflib
from Termpylus_py import mload

try:
    _ = uglobals
except NameError:
    uglobals = dict()
    #uglobals['tmodify'] = set() # Occasionaly check for differences.
    uglobals['edits'] = [] # Edits to files.

def txt_edit(old_txt, new_txt):
    #https://stackoverflow.com/questions/18715688/find-common-substring-between-two-strings
    #https://docs.python.org/3/library/difflib.html
    if old_txt == new_txt:
        return [0,0,''] # Null edit. Please don't add this.
    s = difflib.SequenceMatcher(None, old_txt, new_txt)
    blocks = s.get_matching_blocks() #[(a,b,size)]
    blocks = list(filter(lambda b: b.size>0, blocks))
    # First and last block:
    if len(blocks)==1:
        blocks = [blocks[0], blocks[0]]
    TODO
    return [ix0, ix1, txt_ins]

def record_updates(mname, fname, old_txt, new_txt):
    # Standard record updates.
    # TODO: make it more real time, not just triggered.
    if old_txt is None:
        raise Exception('None old_text; files should be preloaded.')
    ed = txt_edit(old_txt, new_txt)
    t_now = time.time()
    ed1 = [mname, fname]+ed+[t_now]
    uglobals['edits'].append(ed1)

def get_edits():
    return uglobals['edits']
