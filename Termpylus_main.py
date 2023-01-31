# Simple shell wrapper. Will use windows shells on windows and linux shells on linux.
# Warning: This UI design patterns used here don't scale, do not use for larger UI sizes!
#https://www.geeksforgeeks.org/build-a-basic-text-editor-using-tkinter-in-python/
#https://stackoverflow.com/questions/58417529/how-do-i-get-the-tkinter-event-listener-to-work
import tkinter as tk
import traceback, sys
from Termpylus_shell import shellpython
from Termpylus_UI import evt_check, layout, slowprint, hotkeys
from Termpylus_core import updater

debug_show_keypress = False

root = tk.Tk()
root.geometry("1024x768")
root.title("A bit more of terminal")
root.minsize(height=0, width=0)
root.maxsize(height=8192, width=8192)
scrollbar = tk.Scrollbar(root)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def set_text_text(tkinter_txt, str_txt):
    #https://www.geeksforgeeks.org/how-to-set-text-of-tkinter-text-widget-with-a-button/
    tkinter_txt.delete('1.0',"end")
    tkinter_txt.insert('1.0', str_txt)

def debug_keypress(evt):
    mods = evt_check.get_mods(evt)
    if len(mods)>0:
        print('Keypress:', mods, '+', evt.keysym)#, hex(evt.state))
    else:
        print('Keypress:', evt.keysym)#, hex(evt.state))

class GUI(tk.Frame):
    def __init__(self, shell, root=root):
        super(GUI, self).__init__(root)
        self.shell = shell

        self.text_input = tk.Text(root, yscrollcommand=scrollbar.set)
        #self.text_input.bind('<<Modified>>', self.text_changed_callback, add='+')
        root.bind("<Configure>", self.resize, add='+')
        self.text_input.pack() #fill=tk.BOTH

        # Doesn't work: , selectbackground="red", inactiveselectbackground="green"
        self.shell_output = tk.Text(root, yscrollcommand=scrollbar.set, bg = "#EEEEFF")
        self.shell_output.bind('<KeyPress>', self.shell_output_keypresses, add='+')
        self.shell_output.pack()

        self.shell.add_update_listener(self.set_shell_output, dt=0.0625)
        #entry_widget = tk.Entry(root, textvariable=self.string_listener)
        #entry_widget.pack()
        #self.resize([1024, 768])

        self.historybox = tk.Listbox(root, yscrollcommand=scrollbar.set, bg = "#77FF77")
        self.historybox.bind('<Double-1>', self.maybe_click_history, add='+')
        self.historybox.bind('<KeyPress>', self.maybe_click_history, add='+')

        self.historybox.pack()

        self.all_widgets = [self.text_input, self.shell_output, self.historybox]
        layout.add_bigsmall_fns(self.all_widgets); layout.place_all(None, None, self.all_widgets)
        layout.add_fontsize_fns(self.all_widgets)
        layout.focus_cycle(root, self.all_widgets)
        for w in self.all_widgets:
            w.bind('<KeyPress>', self.maybe_send_command, add='+')
            w.bind('<KeyPress>', self.maybe_clear_app, add='+')
            if debug_show_keypress:
                w.bind('<KeyPress>', debug_keypress,  add='+')

    def maybe_click_history(self, evt):
        evt_trigger = evt.keysym =='??' or evt.keysym=='Return' and len(evt_check.get_mods(evt))==0
        if evt_trigger and len(self.historybox.curselection())==1:
            #https://www.tutorialspoint.com/how-do-i-get-the-index-of-an-item-in-tkinter-listbox
            #https://www.geeksforgeeks.org/how-to-get-selected-value-from-listbox-in-tkinter/
            ix = list(self.historybox.curselection())[0]
            txt = self.historybox.get(ix)
            if len(txt.strip())>0:
                set_text_text(self.text_input, txt)
            #print("You have selected " + str(item))

    def set_shell_output(self):
        self.shell_output.delete(1.0, tk.END)

        colors = ["#000099", "#004400", "#770000"]
        ck = len(colors)
        for i in range(ck):
            # https://stackoverflow.com/questions/47591967/changing-the-colour-of-text-automatically-inserted-into-tkinter-widget
            col = colors[i%ck]
            self.shell_output.tag_config('stdout'+str(i), background="#EEEEFF", foreground=col)
            self.shell_output.tag_config('stderr'+str(i), background="yellow", foreground=col)

        for triplet in self.shell.outputs:
            # https://stackoverflow.com/questions/30957085/how-can-i-set-the-text-widget-contents-to-the-value-of-a-variable-in-python-tkin
            ix = triplet[2]
            if triplet[1] is True:
                style = 'stderr'+str(ix%ck)
            else:
                style = 'stdout'+str(ix%ck)

            self.shell_output.insert(tk.END, triplet[0], style)

        #txt = '\n'.join([str(xi) for xi in self.shell['outputs']])

        #https://stackoverflow.com/questions/811532/how-to-scroll-automatically-within-a-tkinter-message-window
        self.shell_output.see(tk.END)

    def shell_output_keypresses(self, *args):
        evt = args[0]
        char = evt.char
        keysym = evt.keysym
        if evt_check.emacs(evt, hotkeys.kys['clear_shell']):
            self.shell.outputs = []
            self.set_shell_output()

    #https://stackoverflow.com/questions/17815686/detect-key-input-in-python
    def maybe_send_command(self, *args):
        #print('Event: ', args[0].__dict__)
        #https://stackoverflow.com/questions/19861689/check-if-modifier-key-is-pressed-in-tkinter
        evt = args[0]
        char = evt.char; char = (char+' ')[0]

        if evt_check.emacs(evt, hotkeys.kys['run_cmd']): # Shift enter = send command.
            mo0 = sys.modules.copy()
            input_to_shell=self.text_input.get("1.0","end-1c")

            autocorrected_input = self.shell.autocorrect(input_to_shell)
            if autocorrected_input != input_to_shell:
                input_to_shell = autocorrected_input
                set_text_text(self.text_input, autocorrected_input)
            self.shell.send(input_to_shell)
            self.shell.input_ix += 1
            if len(input_to_shell)>0 and input_to_shell[-1] == '\n':
                #https://stackoverflow.com/questions/49232866/how-to-delete-last-character-in-text-widget-tkinter
                self.text_input.delete("end-2c", tk.END)
            repeat = False
            if self.historybox.size()>0:
                if self.historybox.get(self.historybox.size()-1).strip()== input_to_shell.strip():
                    repeat = True
            if not repeat:
                self.historybox.insert(tk.END, input_to_shell.strip()+'\n')
                self.historybox.see(tk.END)
            new_modules = set(sys.modules.keys())-set(mo0.keys())
            updater.startup_cache_sources(new_modules)

    def maybe_clear_app(self, *args):
        if evt_check.emacs(args[0], 'C+l'): # Bash default clear.
            self.shell.clear_printouts()
            self.set_shell_output()

    def resize(self, *args):
        try:
            [w,h] = [args[0].width, args[0].height]
        except:
            [w,h] = args[0]
        layout.place_all(w,h,self.all_widgets)

    #def text_changed_callback(self, *args):
        #https://stackoverflow.com/questions/14824163/how-to-get-the-input-from-the-tkinter-text-widget
    #    inputValue=self.text_input.get("1.0","end-1c")
        #print("Text changed to:", inputValue)
        #https://stackoverflow.com/questions/67957098/python-tkinter-bindmodified-works-only-once
    #    self.text_input.edit_modified(False) # Reset the modified flag for text widget.

if __name__=='__main__':
    print_state_singleton = slowprint.PrinterState()
    updater.startup_cache_sources()
    #shell = shellnative.Shell()
    shell = shellpython.Shell()
    try:
        gui = GUI(shell)
        gui.mainloop()
    except Exception:
        traceback.print_exc()
    #print('About to exit shell!')
    shell.exit_shell()
    #sys.exit()
    #print('Exited shell!')
