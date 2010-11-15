#!/usr/bin/env python

import os, sys, subprocess, threading, shutil, glob

_l = [True]
w = lambda v, f = _l.__setitem__: f(0, v) #write
s = lambda str: str.strip() #strip
e = lambda str, suffix = ':': str.endswith(suffix) #endswith
q = lambda: _l[0] #query status
h = lambda i = 0: w(False) and False #Halt
c = lambda i = 0: w(True) or True #Continue
sp = lambda str: map(s, str.split(':')) #Split
d = dict
enu = enumerate
is_path = lambda _p: s(_p) and e(_p) and c()
is_pair = lambda _p: s(_p) and q() and ((not e(_p)) or h())
paths = lambda yml: [(i, pth) for i, pth in enu(yml)]
pairs = lambda _y, _i: [(sp(ln)[0], sp(ln)[1]) for ln in _y[_i + 1:] if is_pair(ln)]
parse_config = lambda lines: d([(pth[:-1], d(pairs(lines, i))) for i, pth in paths(lines) if is_path(pth)])

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

class Worker(threading.Thread):
    def __init__(self, callback, args = None, kwargs = None):
        super(self.__class__, self).__init__()
        self._args = args or []
        self._kwargs = kwargs or {}
        self._callback = callback


    def run(self):
        self._callback(*self._args, **self._kwargs)

process = lambda * args, **kwargs: Worker(subprocess.Popen, args, kwargs)

class Dependency(object):
    def __init__(self, args):
        self._path, self._config = args
        print mycenter(self._path)
        self._path = os.path.normpath(os.path.join(cwd, self._path))
        if not os.path.isdir(self._path):
            print "Creating directory"
            os.makedirs(self._path)

        map(self._requestConfigItem, ('url', 'branch'))

    def _requestConfigItem(self, name):
        value = self._config.get(name, False) or _raise("Required attribute not set: %s" % name)
        setattr(self, '_' + name, value)

    def __call__(self):
        if not os.path.isdir(self._path): raise RuntimeError("Directory magically disappeared!")
        self._checkGitPresence()

    def pull(self):
        pass

    def push(self):
        confirm("Do you want to pull from all repositories?")
        pass

    def _subprocessBuilder(self, command):
        return lambda: self._executeWorker(process(command, cwd = self._path))

    def _checkGitPresence(self):
        return self._subprocessBuilder(['git', 'status'])()



    def install(self):
        install = self._subprocessBuilder(['git', 'init'])
        install()



    def _executeWorker(self, worker):
        try:
            worker.start()
        finally:
            worker.join()

def run():
    print mycenter("Running gploy v0.1")
    with open('meta.yml', 'r') as f:
        #Strip whitespace
        yml = map(s, f.readlines())
        config = parse_config(yml)
        call = lambda x: x()
        deps = map(Dependency, config.iteritems())
        map(call, deps)

if __name__ == "__main__":
    new_path = lambda * args: os.path.join('_gploy', *args)
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
