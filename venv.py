import sys, imp, os

class vEnvError(RuntimeError):
    pass

class vEnv(object):
    def __init__(self):
        self._sourceDir = None
        self._mappings = []
        self._next_file = None

    def setSourceDir(self, dir):
        if os.path.isdir(dir):
            self._sourceDir = dir
        else:
            raise vEnvError("Source directory does not exist.")

    def map(self, virtual, path):
        """Redirect a module import."""
        self._mappings.insert(0, (virtual, path))
        self._sort()

    def _sort(self):
        """
        Sort mappings by length of virtual, descending.
        
        Mappings must be ordered in this fastion because
        we want the best match (most identifiers)
        to be used.
        
        Consider these mappings:
        
        plugins.johndoe.database -> johndoe
        plugins -> plugins
        
        Python code:
        import plugins.johndoe.database
        
        If it was odered the other way around,
        the import would be redirected to plugins
        which is clearly not the goal here.
        Hence we sort by the length, descending
        of the virtual module path.
        
        """
        get_key = lambda map: len(map[0])
        return sorted(self._mappings, key = get_key, reverse = True)

    def find_module(self, module_name, package_path):
        """PEP 302: Module Loader"""
        if not self._sourceDir:
            raise vEnvError("Source dir not set.")

        for virtual, path in self._mappings:
            if module_name.startswith(virtual):
                partial = module_name[len(virtual) + 1:]
                try:
                    if partial:
                        return self._resolve_import(path, partial.split("."))
                    else:
                        return self._resolve_import(path)
                except vEnvError as e:
                    print e
                    return None
        return
    def _resolve_import(self, path, partials = None):
        if partials:
            submodules = partials[:-1]
            path = os.path.join(self._sourceDir, path, *submodules)
            if not os.path.isdir(path):
                raise vEnvError("No such path: %s" % path)
            package = os.path.join(path, partials[-1], '__init__.py')
            module = os.path.join(path, partials[-1]) + '.py'
            if os.path.isfile(package):
                self._next_file = package
            elif os.path.isfile(module):
                self._next_file = module
            else:
                return None
        else:
            # Import entire module
            # Look for __init__.py
            init = os.path.join(self._sourceDir, path, '__init__.py')
            if os.path.isfile(init):
                self._next_file = init
            else:
                raise vEnvError("__init__.py not found in %s" % os.path.dirname(path))
        return self

    def load_module(self, fullname):
        # According to PEP 302:
        # If there is an existing module object named 'fullname' in
        # sys.modules, the loader must use that existing module.
        # (Otherwise, the reload() builtin will not work correctly.)
        # According to PEP 302:
        # If a module named 'fullname' does not exist in sys.modules,
        # the loader must create a new module object and add it to
        # sys.modules.
        if self._next_file:
            ispkg = self._next_file.endswith('__init__.py')
            if fullname in sys.modules:
                return sys.modules[fullname]
            # Load module because not loaded
            with open(self._next_file, 'U') as f:
                if ispkg:
                    description = ("", "", imp.PKG_DIRECTORY)
                else:
                    description = ("", "", imp.PY_SOURCE)
                mod = imp.load_module(fullname, f, self._next_file, description)
                sys.modules[fullname] = mod
                exec f in mod.__dict__
            return mod
        else: raise vEnvError("Invalid next file.")

# Initialize vEnv instance
vEnv = vEnv()
try:
    main_file = sys.modules["__main__"].__file__
    vEnv.setSourceDir(os.path.dirname(main_file))
except:
    pass

def map(virtual, actual):
    """Redirect import."""
    vEnv.map(virtual, actual)

def set_source_dir(dir):
    vEnv.setSourceDir(dir)

sys.meta_path.insert(0, vEnv)
