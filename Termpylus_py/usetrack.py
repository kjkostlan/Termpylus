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
    # If not change or old_txt is None will not make a difference.
    #https://stackoverflow.com/questions/18715688/find-common-substring-between-two-strings
    #https://docs.python.org/3/library/difflib.html
    if old_txt is None or old_txt == new_txt:
        return [0,0,''] # Null edit. Please don't add this.
    if type(old_txt) is not str:
        raise TypeError('Both inputs must be a str but old_txt isnt.')
    if type(new_txt) is not str:
        raise TypeError('Both inputs must be a str but new_txt isnt.')
    s = difflib.SequenceMatcher(None, old_txt, new_txt)
    blocks = s.get_matching_blocks() #[(a,b,size)]

    blocks = list(filter(lambda b: b.size>0, blocks))

    if len(blocks)==0:
        return [0, len(old_txt), old_txt, new_txt]

    # Use the first and last block:
    b0 = blocks[0]; b1 = blocks[-1]
    ax0 = 0 if b0.a>0 else b0.a+b0.size
    ax1 = len(new_txt) if b1.b+b1.size<len(new_txt) else b1.b
    bx0 = ax0+b0.b-b0.a; bx1 = bx0+(ax1-ax0)

    return [ax0, ax1, old_txt[ax0:ax1], new_txt[bx0:bx1]]

def record_updates(mname, fname, old_txt, new_txt):
    # Standard record updates.
    # TODO: make it more real time, not just triggered.
    if old_txt is None:
        raise Exception('None old_text; files should be preloaded.')
    ed = txt_edit(old_txt, new_txt)
    if str(ed)==str([0,0,'']):
        return # No edit made.
    t_now = time.time()
    ed1 = [mname, fname]+ed+[t_now]
    uglobals['edits'].append(ed1)

def get_edits(*args):
    return list(uglobals['edits'])
