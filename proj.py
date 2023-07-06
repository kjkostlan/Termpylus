# Sample proj.py file which should go into the top level of the project folder (and remove this comment).
import os

def _install_gitpacks(): # Runs once on "import proj"
    # Installs stream-handling and code-processing external packages.
    packs = {}
    packs['./Termpylus_extern/fastatine'] = 'https://github.com/kjkostlan/fastatine'
    packs['./Termpylus_extern/slitherlisp'] = 'https://github.com/kjkostlan/slitherlisp'
    packs['./Termpylus_extern/waterworks'] = 'https://github.com/kjkostlan/waterworks'

    try:
        import Termpylus_user_paths
        extern_local_paths = Termpylus_user_paths.extern_local_paths
    except:
        extern_local_paths = {}
    for epath in extern_local_paths.values():
        if '.' in epath:
            raise Exception('Termpylus_user_paths, if specified, should be absolute paths.')

    for k, v in packs.items():
        k = k.replace('\\','/')
        if k == '.' or k[0:2] != './':
            raise Exception('Forgot the ./<folder>')
        if k in extern_local_paths:
            ph = extern_local_paths[k]
            print(f'Local extern code path requested for {k}: {os.path.realpath(ph)}')
            if not os.path.exists(ph):
                raise Exception('But said path does not exist.')
            code_in_a_box.download(ph, k, clear_folder=False)
        else:
            print('No local path specified, using GitHub for:', k)
            code_in_a_box.download(v, k, clear_folder=False)

########################## Boilerplate code below ##############################
########### (some of our pacakges depend on global_get and proj.dump_folder) ##########
def global_get(name, initial_value):
    # Proj, by our convention, also handles is where global variables are stored.
    # Any packages that use Proj should use some sort of qualifier to avoid dict key-collisions.
    # This fn is a get function which sets an initial_value if need be.
    if name not in dataset:
        dataset[name] = initial_value
    return dataset[name]

try:
    did_this_run_yet1
except:
    did_this_run_yet1 = True
    dataset = {} # Store per-session variables here.

    leaf = '/code_in_a_box.py'
    if not os.path.exists('./'+leaf):
        url = f'https://raw.githubusercontent.com/kjkostlan/Code-in-a-Box/main{leaf}'
        os.system(f'curl "{url}" -o "{"./"+leaf}"')
    import code_in_a_box
    _install_gitpacks()
    #os.unlink('./'+leaf) # Optional delete step.
