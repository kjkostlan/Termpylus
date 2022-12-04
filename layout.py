# Widget layout.
# Based on simple priority stuff.

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
    # Alt + and Alt -
    def maybe_change_sz(widget_ix, evt):
        mod_state = evt.state # 4 = ctrl, 1 = shift, 131072 = alt.
        char = evt.char
        fac = 1.0
        if mod_state == 131072 or mod_state==131072+1:
            if char=='-' or char == '_':
                fac = 7.0/8.0
            elif char=='=' or char == '+':
                fac = 8.0/7.0
            if mod_state==131072+1:
                fac = fac**0.25
        if fac != 1.0:
            normalize_widget_sizes(widgets)
            widgets[widget_ix].want_size = widgets[widget_ix].want_size*fac
            place_all(None, None, widgets)

    for i in range(len(widgets)):
        widgets[i].bind('<KeyPress>', lambda evt, j=i: maybe_change_sz(j, evt=evt), add='+')

def add_fontsize_fns(widgets):
    for w in widgets:
        w.lovely_font = ['Courier', 12]
        w.config(font=w.lovely_font)
    def maybe_change_font(w, evt):
        mod_state = evt.state # 4 = ctrl, 1 = shift, 131072 = alt.
        char = evt.char
        keysym = evt.keysym
        delta = 0
        if (mod_state==4 or mod_state==5) and keysym=='equal':
            delta = 1
        elif (mod_state==4 or mod_state==5) and keysym=='minus':
            delta = -1
        if mod_state==5:
            delta = delta*4
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
        mod_state = evt.state # 4 = ctrl, 1 = shift, 131072 = alt.
        char = evt.char
        keysym = evt.keysym
        if keysym=='grave' or keysym=='asciitilde':
            focus = which_has_focus(widgets)
            #print('Current focus:', focus, 'mod_state:', mod_state)
            if focus==-1:
                focus = 0
            if mod_state==4:
                focus = (focus+1)%len(widgets)
            elif mod_state==5:
                focus = (focus-1)%len(widgets)
            if mod_state == 4 or mod_state == 5:
                #print('Set focus:', focus)
                widgets[focus].focus_set()

    for w in widgets:
        w.bind('<KeyPress>', maybe_cycle_focus, add='+')

