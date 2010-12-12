#!/usr/bin/env python

import glob

import os
import shutil
import subprocess
import sys

import console
import modules

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


def namespace(cls):
    return cls()

def singleton(cls, instances = {}):
    def factory():
        instances.setdefault(cls, cls())
        return instances[cls]
    return factory



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



def run():
    print console.center("Running gploy v0.1")
    with open('meta.yml', 'r') as f:
        #Strip whitespace
        config = parse_config(f.readlines())

    call = lambda x: x()
    deps = map(modules.Module, config.iteritems())
    map(call, deps)
    if modules.Module.master:
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
            w("import %s" % modules.Module.master)
            w("%s._gploy()" % modules.Module.master)

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
    print console.center("Welcome to gploy!")
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
    print console.center("gploy setup completed")
    print "let's give this a shot now... shall we?"
    run()
