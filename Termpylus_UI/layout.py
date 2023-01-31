# Widget layout.
# Based on simple priority stuff.
from . import evt_check, hotkeys

def normalize_widget_sizes(widgets):
    # Creates the want_size attribute, and sum to one.
    total = 0.0
    for w in widgets:
        if 'want_size' not in w.__dict__:
            w.want_size = 1.0
        total = total+w.want_size
    for w in widgets:
        w.want_size = w.want_size/total

def place_all(window_x, window_y, widgets):
    normalize_widget_sizes(widgets)
    used_up = 0.0
    for i in range(len(widgets)):
        #https://www.tutorialspoint.com/python/tk_place.htm
        widgets[i].place(relx=0.0, rely=used_up, relwidth=1.0, relheight=widgets[i].want_size)
        used_up = used_up+widgets[i].want_size

def add_bigsmall_fns(widgets):
    # Make a frame bigger or smaller.
    def maybe_change_sz(widget_ix, evt):
        char = evt.char
        fac = 1.0
        _x = hotkeys.kys; facs = {_x['grow_frame']:(8.0/7.0)**0.25, _x['grow_frame_fast']:8.0/7.0, _x['shrink_frame']:(7.0/8.0)**0.25, _x['shrink_frame_fast']:7.0/8.0}
        for k in facs.keys():
            if evt_check.emacs(evt, k):
                fac = facs[k]
        if fac != 1.0:
            normalize_widget_sizes(widgets)
            widgets[widget_ix].want_size = widgets[widget_ix].want_size*fac
            place_all(None, None, widgets)

    for i in range(len(widgets)):
        widgets[i].bind('<KeyPress>', lambda evt, j=i: maybe_change_sz(j, evt=evt), add='+')

def add_fontsize_fns(widgets):
    for w in widgets:
        w.lovely_font = ['Courier', 12] # Probably a lovelier font exists.
        w.config(font=w.lovely_font)
    def maybe_change_font(w, evt):

        _x = hotkeys.kys; deltas = {_x['grow_font']:1, _x['shrink_font']:-1, _x['grow_font_fast']:4, _x['shrink_font_fast']:-4}
        delta = 0
        for k in deltas.keys():
            if evt_check.emacs(evt, k):
                delta = deltas[k]

        if delta != 0:
            w.lovely_font[1] = max(1,int(w.lovely_font[1]+delta+0.5))
            w.config(font=w.lovely_font)
    for w in widgets:
        w.bind('<KeyPress>', lambda evt, wd=w: maybe_change_font(wd, evt=evt), add='+')

def focus_cycle(root, widgets):

    def which_has_focus(widgets):
        w0 = root.focus_get()
        for i in range(len(widgets)):
            if widgets[i] is w0:
                return i
        return -1

    def maybe_cycle_focus(evt):
        char = evt.char
        keysym = evt.keysym
        focus = which_has_focus(widgets)
        if evt_check.emacs(evt, hotkeys.kys['focus_next']):
            focus = (focus+1)%len(widgets)
            widgets[focus].focus_set()
        if evt_check.emacs(evt, hotkeys.kys['focus_prev']):
            focus = (focus-1)%len(widgets)
            widgets[focus].focus_set()

    for w in widgets:
        w.bind('<KeyPress>', maybe_cycle_focus, add='+')
