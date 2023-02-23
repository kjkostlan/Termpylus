# Simple text-based Python parsing. Not intended to handle all use cases; can be tricked once in a while.
import difflib, re

py_kwds = {'import','from','def','lambda','class', 'try','except','raise','assert','finally',\
           'await','async','yield', 'if','or','not','elif','else','and','is', \
           'while','for','in','return','pass','break','continue', \
           'global','with','as','nonlocal',  'del',\
           'False','None','True'}

def simple_tokens(code):
    # Simple tokenize that tries to isolate vars. Not smart about strings.
    pattern = '[ \n\[\]\{\}\(\)\#:\/\-=\+\%\*<>]+'
    return re.split(pattern, code)

def canon_lines(code):
    return code.replace('\r\n','\n').replace('\t','    ').split('\n')

def line_indent_levels(code):
    # Increases on indent, decreased on dedent.
    # Levl is relative to first line.
    # (Do not do too much of this "roll your own" text analysis, there are better libraries for that!)
    code = code.replace('"""',"'''") # reduces triple quote confusions further.
    lines = canon_lines(code)
    spaces = []; last_nsp = 0; in_triple_quote=False
    for l in lines:
        ls = l.strip()
        nsp = len(l+';')-len((l+';').strip())
        if in_triple_quote:
            nsp = last_nsp
            if "'''" in ls or '"""' in ls:
                in_triple_quote = False
        elif ls.startswith('#') or len(ls)==0:
            nsp = last_nsp
        elif ls.startswith("'''") or ls.startswith('"""'):
            in_triple_quote=True
        spaces.append(nsp)
        last_nsp = nsp

    spaces2depth = {}
    last_depth = 0
    out = [0]
    for i in range(1, len(lines)):
        nsp = spaces[i]; nsp0 = spaces[i-1]
        #if nsp>nsp0:
        #    print('Line of indent:', lines[i])
        if nsp==nsp0:
            depth = last_depth
        elif nsp>nsp0:
            depth = last_depth+1
            for i in range(nsp0+1, nsp+1): # Only i=nsp is syntactically allowed.
                spaces2depth[i] = depth
        elif nsp<nsp0:
            depth = spaces2depth.get(nsp,0)
        out.append(depth)
        last_depth = depth
    #print('Spaces:', spaces, 'depths:', out)

    return out

def sourcecode_defs(code, nest=True):
    # Map from var name to def source. Option to nest inside defs and classes.
    # (nested defs will be reported here but are not seen as a module or class attribute).
    lines = canon_lines(code)
    levels = line_indent_levels(code)
    nestings = []
    out = {}
    N = len(lines)
    for i in range(N):
        l0 = lines[i].strip()
        if l0.startswith('def') or l0.startswith('class'):
            vname = (simple_tokens(l0)+['__PARSEERROR__'])[1].strip()
            nestings.append(vname)
            vnamefull = '.'.join(filter(lambda x: len(x)>0, nestings))
            if nest or len(nestings)<=1:
                nsp = len(lines[i])-len(l0)
                src_lines = []
                for j in range(i, len(lines)):
                    nspj = len(lines[j])-len(l0)
                    if nspj<nsp:
                        break
                    src_lines.append((lines[j]+' '*nsp)[nsp:])
                src = '\n'.join(src_lines)
                out[vnamefull] = src
        elif i<N-1 and levels[i+1]>levels[i]:
            nestings.append('') # Non-nesting indent.
        elif i<N-1 and levels[i+1]<levels[i]: # dedent.
            nestings = nestings[0:levels[i+1]]

    return out

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
