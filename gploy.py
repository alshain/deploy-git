#!/usr/bin/env python

import os, sys, subprocess, shutil, glob
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

class Dependency(object):
    def __init__(self, args):
        self._path, self._config = args
        print mycenter(self._path)
        self._path = os.path.normpath(os.path.join(cwd, self._path))
        if not os.path.isdir(self._path):
            print "Creating directory"
            os.makedirs(self._path)
        self._git = lambda * args: self._subprocessBuilder(['git'] + list(args))()
        self._overlay = self._config.get('overlay', None)
        self._overlayBranch = self._config.get('overlay_branch', None)
        self._subdirectory = self._config.get('overlay', None)
        self._overlay = self._config.get('overlay', None)

        map(self._requestConfigItem, ('url', 'branch'))

    def _requestConfigItem(self, name):
        value = self._config.get(name, False) or _raise("Required attribute not set: %s" % name)
        setattr(self, '_' + name, value)

    def __call__(self):
        if not os.path.isdir(self._path): raise RuntimeError("Directory magically disappeared!")
        if not self._gitIsPresent():
            self._install()

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
        return not self._subprocessBuilder(['git', 'status'])()[0]

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

if __name__ == "__main__":
    new_path = lambda * args: os.path.join('_gploy', *args)
    print mycenter("Welcome to gploy!")
    print "Checking git version..."
    version = subprocess.check_output(['git', '--version'])
    version = version[len("git version "):]
    print "Detected: %s" % version
    if not version.startswith("1.7"):
        print "Incompatible GIT version! Expected >= 1.7"
        exit(1)
    if os.path.isfile('../meta.yml'):
        raise RuntimeError("You probably do not want to do this: meta.yml detected in parent directory.")

    files = (
        'gploy.py',
        '.git',
        '.gitignore',
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
