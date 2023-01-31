# Stores global singletons, such as which vars are which, file contents, etc.
# Also has query and "call-when-you-do-this" functions.
try:
    _ = x
except:
    x = 'The below code should only run once!'
    dataset = {}