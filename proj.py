# Sample proj.py file which should go into the top level of the project folder (and remove this comment).

try:
    dump_folder
except:
    dump_folder = './softwaredump' # Software-generated files go here.

def _install_gitpacks(): # Runs once on "import proj"
    # Installs elegant games, for a more socialized age:
    packs = {}
    packs['./Termpylus_extern/fastatine'] = ['https://github.com/kjkostlan/fastatine', '../FaSTatine']
    packs['./Termpylus_extern/slitherlisp'] = ['https://github.com/kjkostlan/slitherlisp', '../Slitherlisp']
    packs['./Termpylus_extern/waterworks'] = ['https://github.com/kjkostlan/waterworks', '../Waterworks']
    dev_mode_local_packs = True # Install from local folders, not from GitHub

    for k, v in packs.items():
        k = k.replace('\\','/')
        if k == '.' or k[0:2] != './':
            raise Exception('Forgot the ./<folder>')
        code_in_a_box.download(v[1 if dev_mode_local_packs else 0], k, clear_folder=False)

    # Package-package interaction which is a bit messy:
    import Termpylus_extern.slitherlisp.cross_package
    Termpylus_extern.slitherlisp.cross_package.integrate(['FaSTatine'], ['Termpylus_extern.FaSTatine'])

########################## Boilerplate code below ##############################
########### (some of our pacakges depend on global_get and proj.dump_folder) ##########
import os
try:
    x
except:
    x = 'The below code should only run once!'
    dataset = {} # Store per-session variables here.

    leaf = '/code_in_a_box.py'
    if not os.path.exists('./'+leaf):
        url = f'https://raw.githubusercontent.com/kjkostlan/Code-in-a-Box/main{leaf}'
        os.system(f'curl "{url}" -o "{"./"+leaf}"')
    import code_in_a_box

    _install_gitpacks()
    #os.unlink('./'+leaf) # Optional delete step.

def global_get(name, initial_value):
    # Proj, by our convention, also handles is where global variables are stored.
    # Any packages that use Proj should use some sort of qualifier to avoid dict key-collisions.
    # This fn is a get function which sets an initial_value if need be.
    if name not in dataset:
        dateset[name] = initial_value
    return dataset[name]
