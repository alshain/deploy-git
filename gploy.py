#!/usr/bin/env python

import os, sys, functools, subprocess, shutil, glob, types
def parse_config(lines):
    strip = lambda str: str.strip()
    lines = map(strip, lines)
    sections = {}
    for line in lines:
        if line.endswith(":"):
            sections[line[:-1]] = section = {}
        elif sections:
            splitted = line.split(':')
            if len(splitted) > 1:
                key = splitted[0].strip()
                value = ":".join(splitted[1:]).strip()
                section[key] = value
    return sections

cwd = sys.path[0]
mycenter = lambda str: str.center(30, '-').center(40, '#')
def _raise(str): raise RuntimeError(str)

def confirm(str):
    print str
    while True:
        answer = raw_input("Enter 'Yes' or 'No': ")
        if answer == "Yes":
            return True
        elif answer == "No":
            raise RuntimeError("Aborting.")

    def run(self):
        self._callback(*self._args, **self._kwargs)


def namespace(cls):
    return cls()

def singleton(cls, instances = {}):
    def factory():
        instances.setdefault(cls, cls())
        return instances[cls]
    return factory

#===========================================================================
# Functional
#===========================================================================

@namespace
class functional(object):
    def map_ind(self, funcs, iterable, fallback = None):
        """
        Map function to item individually.
        
        The fallback parameter is used, when an item has
        no corresponding function.
        
        """
        result = []
        for i, value in enumerate(iterable):
            f = None
            f = funcs[i] if i < len(funcs) else fallback
            if callable(f):
                value = f(value)
            result.append(value)
        return result

    def partial(self, func, *args, **kwargs):
        prt = functools.partial
        partial_ = prt(func, *args, **kwargs)
        partial_.partial = prt(self.partial, partial_)
        return partial_

    def hook_args(self, func, hooks, fallback = None):
        """Apply specific hooks to positional arguments."""
        @functools.wraps(func)
        def hooked(*args, **kwargs):
            args = self.map_ind(hooks, args, fallback)
            return func(*args, **kwargs)
        return hooked

    def hooks_kwargs(self, wrapped, hooks, fallback = None):
        """Apply specific hooks to named arguments."""
        # Gather variable names
        if isinstance(wrapped, types.MethodType):
            # We don't want the self parameter really...
            var_names = wrapped.im_func.func_code.co_varnames
        else:
            var_names = wrapped.func_code.co_varnames

        # Build lookup table key -> func
        # Transform func -> (key1, key2) into key1 -> func, key2 -> func
        key_func = dict()
        for key, value in hooks.iteritems():
            if isinstance(key, str):
                if not callable(value):
                    raise ValueError("Uncallable object provided: %s" % value)
                if key in key_func:
                        raise ValueError("Duplicate key: %s" % key)
                key_func[key] = value
            elif callable(key):
                func, keys = (key, value)
                for key in keys:
                    if key in key_func:
                        raise ValueError("Duplicate key: %s" % key)
                    key_func[key] = func
            else:
                raise ValueError("Uncallable object provided: %s" % value)

        # Build args hook
        hooks = []
        for key in var_names:
            hooks.append(key_func[key] if key in key_func else None)
        def hooked(*args, **kwargs):
            args = self.map_ind(hooks, args)
            processed = kwargs.copy()
            for key, func in key_func.iteritems():
                if key in processed:
                    processed[key] = func(processed[key])
            return wrapped(*args, **processed)
        return hooked

    def process(self, fn, processor):
        """Process args by a function."""
        @functools.wraps(fn)
        def processed(*args, **kwargs):
            args = processor(args)
            return fn(*args, **kwargs)
        return processed

    def joinParam(self, fn, part, append_part = False):
        @functools.wraps(fn)
        def join(*args, **kwargs):
            if append_part:
                return fn(args[0] + part, *args[1:], **kwargs)
            else:
                return fn(part + args[0], *args[1:], **kwargs)

    def chain(self, outer, inner, *args):
        """
        Chain functions
        
        The order in which the functions, in which
        they are passed to the functions, matches
        the way you write them down, if you chain
        them directly.
        
        If you were to do:
            lambda *args, **kwargs: a(b(c(*args, **kwargs)))
        You would call:
            chained(a, b, c)
        
        """
        functions = list(args)
        functions.reverse()
        functions.extend([inner, outer])
        def chained(*args, **kwargs):
            # Call first functions with original arguments
            result = functions[0](*args, **kwargs)
            for func in functions[1:]:
                result = func(result)
            return result
        return chained

    def iterate(self, func, times = 2):
        """Iterate a functions over it's own result."""
        def iterated(arg):
            result = arg
            for i in range(0, times):
                result = func(result)
            return result
        return iterated

#===============================================================================
# venv helper
#===============================================================================

@namespace
class venv(object):
    def __init__(self):
        self._mappings = {}

    def map(self, virtual, actual):
        self._mappings[virtual] = actual

    def getCode(self):
        for virtual, actual in self._mappings.iteritems():
            #virtual = str.strip(virtual)
            #actual = str.strip(actual)
            yield "venv.map(%r, %r)" % (virtual, actual)


#===========================================================================
# ProcessFactory
#===========================================================================

@namespace
class process_factory(object):
    class Process(object):
        class StreamWrapper(object):
            def __init__(self, stream):
                self._stream = stream
                self._buffer = []
            def _print(self, msg):
                print repr(self), msg
            def __getattr__(self, name):
                if not name in ['fileno']:
                    self._print("# Redirecting: %s" % name)
                return getattr(self._stream, name)
            def write(self, data):
                print "###########"
                self._buffer.append(data)
                self._stream.write(data)
                self._stream.flush()
            def getBuffer(self):
                return self._buffer[:]
        def __init__(self, *args, **kwargs):
            print "#" * 79
            print ">> Running `%s`" % " ".join(args[0])
            self._stdout = self.StreamWrapper(sys.stdout)
            self._stderr = self.StreamWrapper(sys.stderr)
            kwargs.setdefault('stdout', self._stdout)
            kwargs.setdefault('stderr', self._stderr)
            self._process = subprocess.Popen(*args, **kwargs)
            self._process.communicate()

    def __init__(self):
        # We are the Borg, resistance is futile!
        # self.__dict__ = self.__shared_state
        pass

    def build(self, command, *args, **kwargs):
        return self.Process(command, *args, **kwargs)

    def partial(self, *args, **kwargs):
        """Create builder with predefined arguments"""
        return functional.partial(self.build, *args, **kwargs)

    def partialCommand(self, command, *args, **kwargs):
        """Return builder default arguments and partial command."""
        def wrapper(command_ammendment, **kwargs):
            merged = command + command_ammendment
            return self.build(merged, **kwargs)
        packer = lambda args: [list(args)]
        wrapper = functional.process(wrapper, packer)
        return functional.partial(wrapper, *args, **kwargs)

class Dependency(object):
    master = None
    def __init__(self, args):
        self._subdirectory, self._config = args
        self._virtual = self._subdirectory
        print mycenter(self._subdirectory)
        self._path = os.path.normpath(os.path.join(cwd, self._subdirectory))
        if not os.path.isdir(self._path):
            print "Creating directory"
            os.makedirs(self._path)
        self._git = process_factory.partialCommand(["git"], cwd = self._path)
        self._overlay = self._config.get('overlay', None)
        self._overlayBranch = self._config.get('overlay_branch', None)

        self._overlay = self._config.get('overlay', None)
        self._alias = self._config.get('alias', None)
        self._master = self._config.get('master', None)

        map(self._requestConfigItem, ('url', 'branch'))

    def _requestConfigItem(self, name):
        value = self._config.get(name, False) or _raise("Required attribute not set: %s" % name)
        setattr(self, '_' + name, value)

    def __call__(self):
        if not os.path.isdir(self._path): raise RuntimeError("Directory magically disappeared!")
        if not self._gitIsPresent():
            pass
            #self._install()

        if self._alias:
            try:
                virtual, actual = map(str.strip, self._alias.split(":"))
                self._virtual = virtual
                venv.map(virtual, os.path.join(self._path, actual))
            except:
                "Could not parse map: %s" % self._alias
                raise
        if self._master:
            if self.__class__.master:
                raise RuntimeError("There can be only one (master).")
            else:
                self.__class__.master = self._virtual

    def pull(self):
        pass

    def push(self):
        confirm("Do you want to pull from all repositories?")
        pass

    def _subprocessBuilder(self, command):
        print ">>> " + " ".join(command)
        return lambda: self._executeSubprocess(
            subprocess.Popen(command, cwd = self._path, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        )

    def _gitIsPresent(self):
        print self._git('status')

    def _install(self):
        self._git('init')
        self._git('remote', 'add', 'origin', self._url)
        self._git('fetch', 'origin')
        self._git('checkout', 'origin/%s' % self._branch, '-b', self._branch)

    def _executeSubprocess(self, process):
        out, err = process.communicate()
        if out:
            print mycenter('Output')
            print out
        if err:
            print mycenter('Error')
            print err
        print ">> ", process.returncode or ">>Success!<<", "\n"
        return (process.returncode, out, err)

def run():
    print mycenter("Running gploy v0.1")
    with open('meta.yml', 'r') as f:
        #Strip whitespace
        config = parse_config(f.readlines())

    call = lambda x: x()
    deps = map(Dependency, config.iteritems())
    map(call, deps)
    if Dependency.master:
        with open('run.py', 'w') as f:
            w = lambda str: f.write(str + '\n')
            w("#!/usr/bin/env python")
            w("from _gploy import venv")
            w("")
            w("# Setting up virtual environment")
            for line in venv.getCode():
                w(line)
            w("")
            w("# Starting application")
            w("import %s" % Dependency.master)
            w("%s._gploy()" % Dependency.master)

def check_git_version():
    print "Checking git version..."
    cmd = ['git', '--version']
    p = subprocess.PIPE
    version = subprocess.Popen(cmd, stdout = p, stderr = p).communicate()[0]
    version = version[len("git version "):]
    print "Detected: %s" % version
    if not version.startswith("1.7"):
        print "Incompatible GIT version! Expected >= 1.7"
        exit(1)

if __name__ == "__main__":
    new_path = lambda * args: os.path.join('_gploy', *args)
    print mycenter("Welcome to gploy!")
    check_git_version()
    if os.path.isfile('../meta.yml'):
        raise RuntimeError("You probably do not want to do this: meta.yml detected in parent directory.")

    files = (
        'gploy.py',
        '.git',
        '.gitignore',
        'venv.py',
    )
    if not os.path.isdir(new_path()):
        print "Creating direcotry: _gploy"
        os.mkdir("_gploy")
    mv = lambda file: shutil.move(file, new_path(file))
    try:
        print "Saving my files..."
        map(mv, files)
        shutil.copy('meta.yml', '_gploy/meta.yml')
        print "Successfully moved our files out of harm's way!"
    except:
        print "Oh... that didn't work so well. Please make sure no files are locked!"
        print "Trying to revert changes..."
        try:
            for file in glob.glob(new_path('*')):
                os.rename(file, os.path.basename(file))
                print "At least this worked - or so I claim ;)"
        except:
            print "Oh well... something's a little off, I guess..."
            print "I have no idea what went wrong - sorry"
        raise
    try:
        print "and make it a module..."
        open(new_path('__init__.py'), 'w').close()
        print "Let's write a startup script..."
        with open('gploy', 'w') as f:
            w = lambda str: f.write(str + '\n')
            w("#!/usr/bin/env python")
            w(" ".join(("from", new_path(), "import gploy")))
            w("gploy.run()")
        os.chmod('gploy', 0744)
    except:
        raise
    print mycenter("gploy setup completed")
    print "let's give this a shot now... shall we?"
    run()
