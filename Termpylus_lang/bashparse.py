# Simple bash-like parsing tools and Python vs bash dection.
# Used in the command line to convert slick bash one-liners to Python and save typing.
# DEFINITELY NOT intended to be a comprehensive bash parser or intrepreter.
# But 90% of what a user types into a bash shell is <10% of the full syntax and is one-line cmds.
    # (And I don't know enough bash!)
    # (A much more comprehesive C implementation: https://github.com/clarity20/bash2py)

#https://www.cyberciti.biz/tips/bash-shell-parameter-substitution-2.html
#https://www.gnu.org/software/bash/manual/html_node/Shell-Parameter-Expansion.html
#https://opensource.com/article/18/5/you-dont-know-bash-intro-bash-arrays
#https://linuxhint.com/simulate-bash-array-of-arrays/     Bash has no nested arrays!?
import sys, re, numba, copy
import numpy as np
from . import pyparse
from Termpylus_shell import pybashlib, hotcmds1

# False: Bash behaves more consistently and intuitivly.
# True: Bash behaves more like Bash.
strict_mode = False

################################### The BASH-runtime world ########################

def BRG(start, end, step=1):
    # Bash range. Can be letter or number range.
    if type(start) is str:
        return [chr(i) for i in range(ord(start),ord(end),step)]
    else:
        return list(range(start, end, step))

def BVC(*items):
    return items

def BEX(*items):
    # Brace expansion. Odd indexes are expanded.
    # See: https://unix.stackexchange.com/questions/402315/nested-brace-expansion-mystery-in-bash
    dims = len(items)
    items1 = []
    if dims==0:
        return ''
    kvals = []
    for i in range(dims):
        if i%2==0:
            kvals.append(1)
            items1.append([str(items[i])])
        elif type(items[i]) is list or type(items[i]) is tuple:
            kvals.append(len(items[i]))
            items1.append([str(itm) for itm in items[i]])
        else:
            kvals.append(1)
            items1.append([str(items[i])])

    ixss = [x.ravel(order='F') for x in np.meshgrid(*[np.arange(k) for k in kvals])]
    out = []
    for i in range(len(ixss)):
        ixs = [ixss[o][i] for o in range(dims)]
        out.append(''.join([items1[j] for j in range(dims)]))

    return out

def BCT(*items):
    # Concatenation with string output.
    return ' '.join(items)

def BIF(cond, if_true, if_false):
    # Requires wrapping the true and false in lambdas.
    return if_true() if bool(cond) else if_false()

def add_bashExpand_fns(module_name):
    # Add functions to the shell's module that are used when expanding one-liners (and staying in a single line).
    # (this is different from the bash commands such as ls).
    m = sys.modules[module_name]
    fns = {'BRG':BRG,'BVC':BVC,'BEX':BEX,'BCT':BCT,'BIF':BIF}
    for k,v in fns.items():
        m.__dict__[k] = v

def option_parse(args, paired_opts):
    # Bash-like handling of arguments.
    # Returns {'flags': [-a, -b, -c, --foo, ...], 'pairs': {"-foo", "bar", ...}, 'tail': [a,b,c]}
    if type(args) is str:
        args = re.split(' +',args)
    paired_opts = set([p.replace('-','') for p in paired_opts])
    out = {'flags':[], 'pairs':{}, 'tail':[]}
    skip = False
    for i in range(len(args)):
        if skip:
            skip = False
            continue
        a = args[i]
        a = a.strip()
        a1 = a+'  '
        if a1[0]=='-' and (a in paired_opts or a.replace('-','') in paired_opts):
            out['pairs'][a] = args[i+1]
            skip = True
        elif a1[0:2]=='--':
            out['flags'].append(a)
        elif a1[0]=='-':
            add_fl = ['-'+c for c in a.replace('-','')]
            out['flags'] = out['flags']+add_fl # One or more single-char flags.
        else:
            out['tail'].append(a)
    return out

################################### The BASH-compiletime world ########################

class Symbol:
    # Symbols are string literals except that they don't get quoted.
    def __init__(self, val):
        self.val = str(val)
    def __str__(self):
        return self.val
    def __repr__(self):
        return self.val

#@numba.njit # The compile time is slower than the time saved in this case (but not in the pyparse case).
def _fsm_core_bash(x):
    #https://devhints.io/bash
    #https://riptutorial.com/bash/example/2465/quoting-literal-text
    #https://tldp.org/HOWTO/Bash-Prog-Intro-HOWTO-5.html
    # Notes:
    #  a=b must not have space around the = else command not found instead of var set.
    #In bash some strings are not quoted (i.e. taken as literals).
    #Note: The bash syntax is very complex. This function is not intended to handle all cases as our use of bash syntax is minimal.

    singleline_comment = False # # = 35; \n = 10,
    colon_comment = False # : = 58, ' = 39. Only recognizes :' or : ' one space (space = 32). : is a do-nothing used in other places.
    double_gt_comment_ix_start = -1 #<<comment\n\ncomment. Note that comment can be replaced with any matching pair of normal txt.
    double_gt_comment_ix_end = -1 # Range check. Reset to -1 when it is no longer in comment mode. Exclusive ix.
    escape = False # Much like Python!
    plus_minus_as_alphanum = True # Most of the time they count.
    quote = 0 # Single and double quotes are also Pythonesque. But we set it to 3 to indicate a naked quote.
    freshness_deluxe = 1 # The first command in a line or $() or after-; is not quote=3 but instead a symbol.
    paren_lev = 0
    in_multiplex_brace = 0
    aln = pyparse.alphanum_status(x)

    N = len(x)

    token_types = np.zeros(N, dtype=np.int32)
    inclusive_paren_nests = np.zeros(N, dtype=np.int32)
    quote_types = np.zeros(N, dtype=np.int32)

    ci1 = -1; ci2 = -1; ci3=-1
    for i in range(N):
        ci = x[i]
        if i<N-1:
            ci1 = x[i+1]
        if i<N-2:
            ci2 = x[i+2]
        if i<N-3:
            ci3 = x[i+3]
        inclusive_paren_nests[i] = paren_lev # Default.

        escape1 = escape; quote1 = quote; double_gt_comment_ix_start1 = double_gt_comment_ix_start
        singleline_comment1 = singleline_comment; colon_comment1 = colon_comment; freshness_deluxe1 = freshness_deluxe
        in_multiplex_brace1 = in_multiplex_brace
        in_comment = singleline_comment or colon_comment or (double_gt_comment_ix_start>-1)
        open_paren = ci==0x28 or ci==0x5B or ci==0x7B
        close_paren = ci==0x29 or ci==0x5D or ci==0x7D
        paren_valid = not escape and (quote==0 or quote==3 or (i>0 and x[i-1]==0x24 and (i==1 or x[i-2] != 0x5C)))
        alni_plus = aln[i] or (plus_minus_as_alphanum and (ci==0x2d or ci==0x2b)) # - and + can act like alpahum sometimes.

        if escape:
            token_types[i] = token_types[i-1]
            escape1 = False
        if quote==1 and not in_comment and not escape:
            if ci==0x27:
                quote1 = 0
            token_types[i] = 3; quote_types[i]=1
        if quote==2 and not in_comment and not escape:
            if ci==0x22:
                quote1 = 0
            elif ci==0x24: # $
                token_types[i] = 2; quote_types[i]=0; freshness_deluxe1=1; quote1 = 0
            token_types[i] = 3; quote_types[i]=2
        if quote==3 and not in_comment and not escape:
            if ci==0xA or ci==0x20 or ci==0x9: # Space newline.
                quote1 = 0; token_types[i] = 0; quote_types[i]=0
            elif ci==0x24: # $
                token_types[i] = 2; quote_types[i]=0; freshness_deluxe1=1; quote1 = 0
            else:
                token_types[i] = 3; quote_types[i]=3
        if singleline_comment:
            if ci==0xA:
                token_types[i] = 0
                singleline_comment1 = False
            else:
                token_types[i] = 6
        if colon_comment:
            if ci==0x27:
                colon_comment1 = False
            token_types[i] = 6
        if double_gt_comment_ix_start>-1 and not escape:
            if aln[i]>0: # Ignores plus_minus_as_alphanum I think.
                all_match = True
                K = double_gt_comment_ix_end - double_gt_comment_ix_start
                for j in range(K): # Equal token check.
                    j0 = double_gt_comment_ix_start+j; j1 = i-K+j+1 # When j = K-1 we get j1 = i is the last letter.
                    if j1>=N or x[j1] != x[j0]:
                        all_match = False; break
                if all_match:
                    double_gt_comment_ix_start1 = -1
                    double_gt_comment_ix_end = -1
        if paren_valid and close_paren:
            freshness_deluxe1 = 0 # It forces a quote next.
            in_multiplex_brace1 = 0 # Clear.
        if ci==0x5C and not in_comment and not escape:
            escape1 = True
        if not escape and not in_comment and quote==0:
            if alni_plus>0 and freshness_deluxe==0:
                token_types[i] = 3; quote1 = 3; quote_types[i]=3
            if alni_plus>0 and freshness_deluxe>0:
                token_types[i] = 1
            if ci==0x20 or ci==0x29 and freshness_deluxe>0:
                freshness_deluxe1 = 0
            if ci==0xA: # Newline or ; makes things very fresh.
                freshness_deluxe1 = 1
            if ci==0x3D: # = sign quotes the next thing.
                freshness_deluxe1 = 0
            if (ci==0x20 or ci==0xA or ci==0x9) and ci1==0x23: # Space/newline then # enters in a comment.
                singleline_comment1 = True
            if i==0 and ci==0x23:
                singleline_comment1 = True; token_types[i] = 6
            if ci==0x24: # dollar sign breaks the quote.
                freshness_deluxe1 = 1
                token_types[i] = 2
            if ci==0x2a or ci==0x2f or ci==0x25 or ci==0x3d or ci==0x26 or ci==0x7c or ci==0x5e or ci==0x3e or ci==0x3c or ci==0x7e or ci==0x40 or ci==0x2e or (not plus_minus_as_alphanum and (ci==0x2d or ci==0x2b)):
                token_types[i] = 2 #Maybe more symbolic chars belong here?
            if (ci==0x20 or ci==0xA) and ci1==0x3A and (ci2==0x27 or (ci2==0x20 and ci3==0x27)): # The :'  comment.
                colon_comment1 = True; token_types[i] = 6
            if ci==0x27:
                quote1 = 1; token_types[i] = 3; quote_types[i]=1
            if ci==0x22:
                quote1 = 2; token_types[i] = 3; quote_types[i]=2
        if open_paren and paren_valid:
            paren_lev = paren_lev+1; token_types[i] = 4
            inclusive_paren_nests[i] = paren_lev
            quote_types[i]=0 # just for the paren itself.
        if close_paren and paren_valid:
            paren_lev = paren_lev-1; token_types[i] = 5
            quote_types[i]=0
        if (escape or ci != 0x24) and ci1==0x7B and (quote==3 or quote1==3):
            in_multiplex_brace1 = 1 # Special multiplex braces make the commas into spaced tokens.

        if in_multiplex_brace and not escape and ci==0x2C:
            token_types[i] = 0 # Commas in the special brace expansion.
        escape = escape1; quote = quote1; double_gt_comment_ix_start = double_gt_comment_ix_start1
        singleline_comment = singleline_comment1; colon_comment = colon_comment1; freshness_deluxe = freshness_deluxe1
        in_multiplex_brace = in_multiplex_brace1

    return token_types, inclusive_paren_nests, quote_types

def fsm_parse_bash(txt):
    #token, paren, quote_type
    x = np.frombuffer(txt.encode('UTF-32-LE'), dtype=np.uint32)
    return _fsm_core_bash(x)

class ParsedStr():
    def __init__(self, txt, python=False):
        x = np.frombuffer(txt.encode('UTF-32-LE'), dtype=np.uint32)
        self.txt = txt
        if python:
            self.token, self.paren, _ = pyparse.fsm_parse(txt)
            self.quote = -1*np.ones_like(self.token) # Not calculated.
        else:
            self.token, self.paren, self.quote = _fsm_core_bash(x)

    def closing_paren_ix(self, ix):
        lev = self.paren[ix]
        for i in range(ix+1, len(self.txt)):
            if self.paren[i]==lev and self.token[i]==5:
                return i
        print('Substring no close from '+str(ix)+':', self.txt)
        raise SyntaxError('Bash substring has no closing paren ix from: '+str(ix))

    def substring(self, ix0, ix1=None):
        out = copy.copy(self)
        if ix1 is None:
            out.txt = self.txt[ix0:]
            out.token = self.token[ix0:]
            out.paren = self.paren[ix0:]
            out.quote = self.quote[ix0:]
        else:
            out.txt = self.txt[ix0:ix1]
            out.token = self.token[ix0:ix1]
            out.paren = self.paren[ix0:ix1]
            out.quote = self.quote[ix0:ix1]
        return out

    def join(pstrs, spaces=0):
        out = ParsedStr('')
        for s in pstrs:
            out.txt = out.txt+(' '*spaces)+s.txt
            out.token = out.token+([0]*spaces)+s.token
            paren = 0; tok = 0
            if len(out.paren)>0:
                paren = out.paren[-1]; tok = out.token[-1]
            elif len(s.paren)>0:
                paren = s.paren[0]; tok = s.token[0]
            out.paren = out.paren+([paren]*spaces)+s.paren
            out.quote = out.quote+([tok]*spaces)+s.quote
        if spaces>0:
            out.txt = out.txt[0:-spaces]
            out.paren = out.paren[0:-spaces]
            out.quote = out.quote[0:-spaces]
        return out

    def substrings(self, ixs0, ixs1):
        return [self.substring(ixs0[i], ixs1[i]) for i in range(len(ixs0))]

    def strip(self):
        if len(self.txt.strip())==len(self.txt):
            return self
        ix0 = len(self.txt)-len(self.txt.lstrip())
        ix1 = -(len(self.txt)-len(self.txt.rstrip()))
        if ix1==0:
            ix1 = None
        return self.substring(ix0, ix1)

    def __str__(self):
        return self.txt
    def __repr__(self):
        return 'ParsedStr('+self.txt+')'

def spacetoken_split(ptxt:ParsedStr):
    # Returns the pieces with the space removed.
    # (only does the outer level)
    ptxt = ptxt.strip()
    ixs0 = []; ixs1 = []; N = len(ptxt.txt)
    if N==0:
        return []
    lev0 = ptxt.paren[0]-(ptxt.token[0]==4)
    for i in range(0, N):
        levi = ptxt.paren[i]-(ptxt.token[i]==4)-(ptxt.token[i]==5)
        if levi>lev0 and i<N-1:
            continue
        sp = ptxt.token[i]==0
        sp0 = i==0 or ptxt.token[i-1]==0
        sp1 = i==N-1 or ptxt.token[i+1]==0
        if not sp and sp0:
            ixs0.append(i)
        if not sp and sp1:
            ixs1.append(i+1)
    return ptxt.substrings(ixs0, ixs1)

def semicolon_split(ptxt:ParsedStr):
    # Returns a list using unescaped semicolons to split.
    # (only does the outer level)
    ptxt = ptxt.strip()
    ixs0 = []; ixs1 = []; N = len(ptxt.txt)
    lev0 = ptxt.paren[0]-(ptxt.token[0]==4)
    for i in range(0, N):
        levi = ptxt.paren[i]-(ptxt.token[i]==4)-(ptxt.token[i]==5)
        if levi>lev0 and i<N-1:
            continue
        sq = ptxt.txt[i]==';' and ptxt.token[i] !=0
        sq0 = i==0 or (ptxt.txt[i-1]==';' and ptxt.token[i-1] !=0)
        sq1 = i==N-1 or (ptxt.txt[i+1]==';' and ptxt.token[i+1] !=0)

        if not sq and sq0:
            ixs0.append(i)
        if not sq and sq1:
            ixs1.append(i+1)

    return ptxt.substrings(ixs0, ixs1)

def standard_split(ptxt:ParsedStr):
    pieces = sum([spacetoken_split(chunk) for chunk in semicolon_split(ptxt)], [])
    return [p.strip() for p in pieces]

def keyword_chunk(ptxts, enter_kwd, intermediate_kwds, exit_kwd, concat=False):
    # The stuff between the kwds.
    if len(kwds)<2:
        return []
    kw_ix = 0; ix0 = -1
    chunks = []; cur_chunk = []
    level = 0; intermediate_kwds = set(intermediate_kwds)
    for i in range(len(ptxts)):
        v = ptxts[i].txt
        if v==enter_kwd:
            level = level+1
        elif level==1:
            if v in intermediate_kwds or v==exit_kwd:
                chunks.append(cur_chunk); cur_chunk = []
            else:
                cur_chunk.append(ptxts[i])
        elif v==exit_kwd:
            level = level-1
    if concat:
        return [ParsedStr.join(ch, 1) for ch in chunks]
    return chunks

def fortran_flavor_tag_chunk(ptxts):
    # Splits by 'if' and 'fi' and by 'for'/'while' and 'done'
    # (outer level only and unlike if_chunk and for_chunk it includes the tokens).
    chunks = []; lev = 0; chunk = []
    N = len(ptxts)
    for i in range(N):
        txt = ptxts[i].txt.strip()
        dig = txt=='for' or txt=='while'
        undig = txt=='fi' or txt=='done'
        if i==N-1 or (lev==1 and undig):
            chunk.append(ptxts[i])
            chunks.append(chunk); chunk = []
        elif lev==0 and dig:
            chunks.append(chunk); chunk = [ptxts[i]]
        else:
            chunk.append(ptxts[i])
    return chunks

def comma_split(ptxt:ParsedStr):
    ptxt = copy.copy(ptxt); ptxt.txt = ptxt.txt.replace(',',' ')
    return spacetoken_split(ptxt)

def double_dot_split(ptxt:ParsedStr):
    ptxt = copy.copy(ptxt)
    for i in range(len(ptxt.txt)-1):
        if ptxt.txt[i]=='.' and ptxt.txt[i+1]=='.' and ptxt.token[i] !=3 and ptxt.token[i] !=6:
            ptxt.token[i]=0; ptxt.token[i+1]=0
    ptxt.txt = ptxt.txt.replace('..',' ')
    return spacetoken_split(ptxt)

def if_chunk(ptxts):
    # Returns [cond, if true, if false] if there is an if, or a length 1 array if there is no if.
    # (if false may be empty []).
    pieces = spacetoken_split(ptxt)
    if ptxts[0].txt=='if':
        for p in ptxts:
            if p.txt=='elif':
                raise SyntaxError('elif statement not supported by this limited bash parser.')
        out = keyword_chunk(ptxt, ['if', {'then', 'else'}, 'fi'], False)
        if len(out) !=2 and len(out) != 3:
            raise Exception('Cant split if statement properly.')
        return out
    return [ptxts] # Length one list = not split.

def for_chunk(ptxts):
    # Splits into the for body and do.
    if ptxts[0].txt=='for':
        out = keyword_chunk(ptxt, ['for', {'do'}, 'done'], True)
        return out
    return [ptxts] # Length one list = not split.

def var_paren_split(ptxt:ParsedStr):
    # ffoo${bar}(baz)abc$123 => ffoo, ${bar}, (baz), abc, $123
    # (outer level only)
    # (use when brace_multiplex_split fails)
    ix0 = 0; ix = 0
    N = len(ptxt.txt)
    if N<2:
        return [ptxt]
    out = []
    lev0 = ptxt.paren[0]-(ptxt.token[0]==4)
    while ix<N:
        c = ptxt.txt[ix]
        lev = ptxt.paren[ix]-(ptxt.token[ix]==4)-(ptxt.token[ix]==5)
        if lev>lev0:
            raise Exception('The closing ix did not work!?')
        if ix==N-1 and ix0<ix:
            out.append(ptxt.substring(ix0,ix+1))
        if ix<N-1:
            c1 = ptxt.txt[ix+1]
        if ptxt.token[ix]==6 or ptxt.token[ix]==3:
            ix = ix+1
        elif c=='$' and (c1=='(' or c1=='[' or c1=='{'):
            if ix>ix0:
                out.append(ptxt.substring(ix0,ix))
            ix1 = ptxt.closing_paren_ix(ix+1)
            out.append(ptxt.substring(ix,ix1+1))
            if ix1+1<=ix:
                raise Exception('Oops!')
            ix0 = ix1+1; ix = ix1+1
        elif c=='$':
            if ix>ix0:
                out.append(ptxt.substring(ix0,ix))
            ix0 = ix; ix = ix+1
        elif c=='(' or c=='[' or c=='{':
            if ix>ix0:
                out.append(ptxt.substring(ix0,ix))
            ix1 = ptxt.closing_paren_ix(ix)
            out.append(ptxt.substring(ix,ix1+1))
            if ix1+1<=ix:
                raise Exception('Oops!')
            ix0 = ix1+1; ix = ix1+1
        else:
            ix = ix+1
    return out

def brace_multiplex_split(ptxt:ParsedStr):
    # foo{bar,baz}123
    # (outer level only)
    ix0 = 0; ix = 0
    N = len(ptxt.txt)
    if N<2:
        return [ptxt]
    out = []
    while ix<N:
        c = ptxt.txt[ix]
        if ix==N-1 and ix0<ix:
            out.append(ptxt.substring(ix0,ix))
        if ix<N-1:
            c1 = ptxt.txt[ix+1]
        if ptxt.token[ix]==6 or ptxt.token[ix]==3:
            ix = ix+1
        elif c=='$' and c1=='{':
            ix = ix+2 # The brace expand forbids ${.
        elif c=='{':
            if ix>ix0:
                out.append(ptxt.substring(ix0,ix))
            ix1 = ptxt.closing_paren_ix(ix)
            if ix1<ix:
                raise Exception('Oops!')
            out.append(ptxt.substring(ix,ix1+1))
            ix0 = ix1+1; ix = ix1+1
        else:
            ix = ix+1
    return out

def eq_split(ptxt:ParsedStr):
    ptxt1 = copy.copy(ptxt)
    for i in range(len(ptxt1.txt)):
        if ptxt1.txt[i]=='=' and ptxt1.token[i] !=3 and ptxt1.token[i] !=6:
            ptxt1.token[i]=0
    ptxt1.txt = ptxt1.txt.replace('=',' ')
    return spacetoken_split(ptxt1)

def _ast_core(ptxts):
    if len(ptxts)>1: # Space-seperated statements.
        fchunks = fortran_flavor_tag_chunk(ptxts[1:])
        if len(fchunks)>1:
            processed_chunks = []
            for ch in fchunks:
                cif = if_chunk(ch)
                cfor = for_chunk(ch)
                cwhile = while_chunk(ch)
                if len(cif)>0:
                    x=[Symbol('BIF'), _ast_core(cif[0])]+[[Symbol('lambda'), [], _ast_core(c)] for c in if_chunk[1:]]
                    processed_chunks.append(x)
                elif len(cfor)>0:
                    x=[Symbol('for')]+[_ast_core(c) for c in cfor]
                elif len(cwhile)>0:
                    x=[Symbol('while')]+[_ast_core(c) for c in cwhile]
                else:
                    x = _ast_core(ch)
            return [Symbol(ptxts[0].txt)]+processed_chunks
        else:
            return [Symbol(ptxts[0].txt)]+[_ast_core([p]) for p in ptxts[1:]]

    ptxt = ptxts[0]
    recur = lambda ptxt1: _ast_core(standard_split(ptxt1))
    pieces = eq_split(ptxt)
    if len(pieces)>1: # Should only have 2 pieces.
        return [Symbol('=')]+[recur(pieces[0]), recur(pieces[1])]
    pieces = var_paren_split(ptxt)
    if len(pieces)>1:
        #https://stackoverflow.com/questions/2188199/how-to-use-double-or-single-brackets-parentheses-curly-braces
        pieces1 = brace_multiplex_split(ptxt) # foo{bar,baz}123
        if len(pieces1)>1: # This one is annoying and takes priority.
            out = []
            for i in range(len(pieces1)):
                p = pieces1[i]
                is_braced = p.txt[0]=='{'
                if len(out)%2==0 and is_braced:
                    out.append('') # Empty space so that BEX treats it as not having {}.
                if is_braced:
                    p1 = p.substring(1,-1)
                    dsplit = double_dot_split(p1)
                    csplit = comma_split(p1)
                    if len(csplit)>1:
                        out.append([Symbol('ARR')]+[recur(pi) for pi in csplit])
                    elif len(dsplit)>1: # Range specified.
                        out.append([Symbol('BRG')]+[recur(ds) for ds in dsplit])
                    else:
                        out.append([Symbol('ARR'), recur(p1)])
                else:
                    out.append(recur(p))
            return [Symbol('BEX')]+out

        # Vanilla split and deal with array access:
        processed = []
        for i in range(len(pieces)):
            if i>0 and pieces[i].txt[0]=='[':
                processed[i-1] = [Symbol('ARR'), processed[i-1], recur(pieces[i].substring(1,-1))]
            else:
                processed.append(recur(pieces[i]))
        return [Symbol('BCT')]+processed

    # Leaf cases (but once the outer level is stripped may not be leaf):
    txt = ptxt.txt
    if len(txt)==0: # Does this ever happen?
        raise SyntaxError('Ast parse attempt on empty substring.')
    if len(txt)==1:
        return str(txt) if ptxt.token[0]==3 else Symbol(txt)
    if txt[0]=='$':
        if txt[1]=='(' and txt[2]=='(':
            raise SyntaxError('Arithmetic parsing not supported in this limited bash parser.')
        elif txt[1]=='(': # $(this statement is evaled)
            return recur(ptxt.substring(2, -1))
        elif txt[1]=='[': # $[] and if [ ... ] are both booleans.
            return [Symbol('bool'), ptxt.substring(1, -1)]
        #https://stackoverflow.com/questions/5163144/what-are-the-special-dollar-sign-shell-variables
        elif txt[1] in '0123456789@*#':
            raise SyntaxError('Bash script name and positional parameters not supported in this limited bash parser.')
        elif txt[1]=='-':
            raise SyntaxError('Current shell options set not supported in this limited interpreter.')
        elif txt[1]=='$':
            return [Symbol('pid')]
        elif txt[1:4]=='IFS':
            return ' \t\n'
        elif txt[1]=='_':
            return Symbol('_')
        elif txt[1]=='?':
            raise SyntaxError('Foreground pipeline exit status not supported in this limited bash parser.')
        elif txt[1]=='!':
            raise SyntaxError('PID of the most recent background command not supported in this limited bash parser.')
        else:
            return Symbol(txt[1:]) # Should always be leaf.
    if txt[0]=='[' and txt[1]=='[': # Booleans
        return [Symbol('bool'), recur(ptxt.substring(2, -2))]
    elif txt[0]=='[':
        return [Symbol('bool'), recur(ptxt.substring(1, -1))]
    elif txt[0]=='(': # () without $ makes an array (bash has no nested arrays!).
        [Symbol('BCT')]+recur(ptxt.substring(1, -1))
    elif ptxt.token[0]==1: # A symbol, to be called as a fn.
        return [Symbol(txt)]
    elif ptxt.token[0]==3: # A string.
        return txt

def ast_bash(txt):
    # Nested list AST. The intermediate step in bash2python.
    #https://www.gnu.org/savannah-checkouts/gnu/bash/manual/bash.html#Shell-Expansions
    #https://unix.stackexchange.com/questions/270274/how-to-understand-the-order-between-expansions
    #https://stackoverflow.com/questions/5163144/what-are-the-special-dollar-sign-shell-variables
    ptxt = ParsedStr(txt)
    pieces = standard_split(ptxt)
    return _ast_core(pieces)

def ast2py(ast_obj):
    # The simplified rules of the the AST subset we support makes it easier.
    # (Still not designed to be comprehensive; Termpylus *isn't* a bash interpreter).
    if type(ast_obj) is list or type(ast_obj) is tuple:
        if len(ast_obj)==0:
            return "[]"
        ast_txts = [ast2py(o) for o in ast_obj]
        x0 = ast_obj[0].val
        if x0=='for': # This code probably doesn't work...
            return "["+ast_txts[1]+' for '+ast_txts[0]+']'
        elif x0=='while': # Maybe we need an industrial strength parser...
            return "["+ast_txts[1]+' while '+ast_txts[0]+']'
        elif x0=='lambda':
            return 'lambda '+','.join(ast_txts[1])+': '+ast_txts[2]
        elif x0 in {'+','-','*','/','%','^','+=','-=','*=','/=','=','==','&','&&','|','||'}:
            return ast_txts[1]+' '+x0+' '+ast_txts[2]
        else:
            return ast_txts[0]+'('+', '.join(ast_txts[1:])+')'
    elif type(ast_obj) is str:
        if "'" not in ast_obj: # Cleaner than repl for strings containing quotes.
            return str('"')+ast_obj+str('"')
        elif '"' not in ast_obj:
            return str("'")+ast_obj+str("'")
        return ast_obj
    else: # Symbols, numbers, etc.
        return str(ast_obj)

def add_varset(ast_obj):
    # The result of the command should go into a varible.
    wrap = False
    if type(ast_obj) is not list and type(ast_obj) is not tuple:
        wrap = True
    elif len(ast_obj) != 3:
        wrap = True
    elif ast_obj[0].val != '=':
        wrap = True

    if wrap:
        return [Symbol('='), Symbol('_'), ast_obj]
    else:
        return ast_obj

def bash2py(txt, prepend_spaces=0):
    tree = ast_bash(txt)
    tree1 = add_varset(tree)
    out = ast2py(tree1)
    if prepend_spaces>0:
        return '\n'.join([' '*prepend_spaces + l for l in out.split('\n')])
    return out

################################### BASH vs python ########################

def lines_vs_python(code, striplines=True):
    # Per line parsing, returns Ptxt array.
    code = code.replace('\r\n','\n')
    lines = code.split('\n'); N = len(lines)
    st_ixs = pyparse.line_start_ixs(code)
    en_ixs = [st_ixs[i]+len(lines[i]) for i in range(N)] #en_ix[i]+1=start_ix[i+1]

    plines = ParsedStr(code, python=True).substrings(st_ixs, en_ixs)
    if striplines:
        plines = [pline.strip() for pline in plines]
    return plines

def is_line_bash(pline_py, assert_decision=True):
    # Decide between bash and python, for a single line.
    # Looks for key syntatical hints (namely the $ and a space between tokens).
    # Can be overiden with a trailing #!bash/#!python.
    line = pline_py.txt; tok_py = pline_py.token; paren_py = pline_py.paren

    if len(line)>0 and pline_py.quote[0] >-1: # not python.
        raise Exception('Pline must be with python=True')

    if len(line.strip())<len(line):
        raise Exception('The line must be stripped in a way to preserve the arrays.')
    line1 = line.replace('2','3').replace('3','')
    if line1.endswith('#!/bin/bash') or line.endswith('#!bash'):
        return True
    if line1.endswith('#!/bin/python') or line1.endswith('#!python'):
        return False

    if len(line)==0 or line.startswith('#'):
        return False # Empty line either way.
    if tok_py[0]==3 or tok_py[0]==6 or (paren_py[0]-(tok_py[0]==4))>0:
        return False # Part of a multiline blob.

    line_ord = np.asarray([ord(c) for c in line])
    line_ord[tok_py==3] = ord('A'); line_ord[tok_py==6] = ord(' ') # Comments to spaces.

    line_deblobbed = ''.join([chr(c) for c in line_ord])
    line_ord[paren_py>0] = ord('A')
    is_outerlev = np.asarray(paren_py)==0
    line_deblobbed2 = ''.join([chr(c) for c in line_ord])

    tok_deb = set(line_deblobbed2.split(' '))
    if 'if' in tok_deb and 'else' in tok_deb:
        return False # 1line if-else statements.

    sub_lines = line_deblobbed.split(';')
    for sub_line in sub_lines:
        if (sub_line.strip().split(' ')+['...'])[0] in pyparse.py_kwds:
            return False # "import foo" has a bash-like syntax but is actually Python.

    if '$' in line_deblobbed:
        return True # $ is never valid python syntax unless it is buried in a quote/comment.
    if re.search('[a-zA-Z0-9] +[a-zA-Z0-9]', line_deblobbed2) is not None:
        return True # "foo bar" *at the outer indent level* means bash.
    if len(line_deblobbed2.replace(' =','=').replace('= ','='))<len(line_deblobbed):
        return False # Outer level foo = bar *with a space* before or after the = means Python.
    if re.match('^[a-zA-Z0-9]+$', line) is not None:
        return True # One token command such as "ls"

    if assert_decision:
        raise SyntaxError('Couldnt classify this line as bash or python (ambigious or this fn is incomplete): '+line)
    else:
        return None # Neither True nor False. Maybe better to treat as Python?

def maybe_bash2py_console_input(txt):
    # Converts bash to python when it detects lines of bash.
    # Python vs bash is decided *per line*.
    if strict_mode:
        raise Exception('Strict mode will only be supported if a lot of bash is used; it would be generally less powerful since it makes it harder to nest statements, etc.')
    txt = txt.strip().replace('\r\n','\n')
    plines = lines_vs_python(txt, striplines=True)
    lines = [pline.txt for pline in plines]

    if len(lines)==0:
        return ''

    line0 = lines[0].replace('2','3').replace('3','')
    if line0=='#!/bin/python' or line0=='#!python':
        return '\n'.join(lines)
    if line0=='#!/bin/bash' or line0=='#!bash':
        for i in range(len(lines)):
            lines[i] = bash2py(lines[i])
        return '\n'.join(lines)

    prev_bash = False
    for i in range(len(lines)):
        is_bash = is_line_bash(plines[i], False)
        if is_bash or (is_bash==None and prev_bash):
            prev_bash = True
            lines[i] = bash2py(lines[i])
        else:
            prev_bash = False

    return '\n'.join(lines)
