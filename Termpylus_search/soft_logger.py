# Uses heuristics in terms of what logs to keep (as to not intefere with performance).
from Termylus_extern.waterworks import ppatch, var_watch
# globals=sys.modules[__name__].__dict__

'''
var_watch.rm_fn_watcher(modulename, var_name)
var_watch.add_fn_watcher(modulename, var_name, f_code=None)
var_watch.with_watcher(modulename, var_name, args, return_log=False)

var_watch.remove_module_watchers(modulename)
var_watch.add_module_watchers(modulename)
var_watch.just_after_module_update(modulename) # Should be called automatically.

var_watch.get_logs(modulename, var_name)
var_watch.get_all_logs()

var_dict = ppatch.get_vars(modulename, nest_inside_classes=True)

dquery.get_all_sourcevars()
dquery.source_find(*bashy_args)
dquery.pythonverse_find(*bashy_args, pythonverse_verse=None, exclude_Termpylus=False) # Not yet written.
ppatch.is_modified(modulename, varname)
'''
