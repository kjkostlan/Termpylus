# Check if keyboard is something, etc.
def get_mods(evt, kprint=False):
    # Returns a string, i.e. CMS
    # https://stackoverflow.com/questions/19861689/check-if-modifier-key-is-pressed-in-tkinter
    #mods = [[0x0001, 'S'], [0x0002,''], [0x0004, 'C'], [0x0008, 'M'], [0x0010,''],[0x0080,'M'],\
    #        [0x0100,''],[0x0200, ''], [0x0400, '']]
    mods = [[0x00001, 'S'], [0x00004,'C'], [0x20000, 'M']]
    mod_state = evt.state # an int.
    out = ''
    for m in mods:
        if mod_state & m[0] != 0:
            out = out+m[1]

    if kprint:
        print('Key mods:', out, 'Mod_state:', hex(mod_state))
    return out

def emacs(evt, emacs_hotkeys):
    # A single hotkey, or multible hotkeys as a list.
    # CMA+x.

    mod_state = evt.state
    char = evt.char
    keysym = evt.keysym.lower()
    evt_mods = get_mods(evt).lower()
    #print('Symbol:', keysym, 'emacs_evt:', emacs_hotkeys)
    key_map = {}
    def _plc(pk):
        for k in pk:
            key_map[k] = pk
    _plc(['ent','enter','ret','return'])
    _plc(['equal','plus','=','+']) # + can't be really used since we split by +.
    _plc(['minus','underscore','-','_'])
    _plc(['asciitilde','grave','`','~'])

    #if '+' in str(emacs_hotkeys):
    #    print('Evt:', [keysym, evt_mods],'hk:',emacs_hotkeys)

    if type(emacs_hotkeys) is str:
        emacs_hotkeys = [emacs_hotkeys]
    for hk in emacs_hotkeys:
        if '+' in hk:
            pieces = hk.split('+')
            mods = pieces[0].lower()
            ky = pieces[1].lower()
        else:
            mods = ''
            ky = hk.lower()
        mod_match = set(mods)==set(evt_mods)
        #print('Stuff:', emacs_hotkeys, [ky, mods], 'vs' , [keysym, get_mods(evt)], 'MODMATCH:', set(mods), set(get_mods(evt)))
        if mod_match:
            aliases = key_map.get(keysym, [keysym])

            for al in aliases:
                if al.lower()==ky:
                    #print('Match on:', [keysym, evt_mods], 'vs:', hk)
                    return True
    return False
