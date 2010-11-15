import os, sys

_l = [True]
w = lambda v, f = _l.__setitem__: f(0, v) #write
s = lambda str: str.strip() #strip
e = lambda str, suffix = ':': str.endswith(suffix)
q = lambda: _l[0]
h = lambda i = 0: w(False) and False
c = lambda i = 0: w(True) or True
sp = lambda str: map(s, str.split(':'))
d = dict
enu = enumerate
is_path = lambda _p: s(_p) and e(_p) and c()
is_pair = lambda _p: s(_p) and q() and ((not e(_p)) or h())
paths = lambda yml: [(i, pth) for i, pth in enu(yml) if is_path(pth)]
pairs = lambda _y, _i: [(sp(ln)[0], sp(ln)[1]) for ln in _y[_i + 1:] if is_pair(ln)]
parse_config = lambda lines:d([(pth, d(pairs(lines, i))) for i, pth in paths(lines)])

with open('meta.yml', 'r') as f:
    yml = map(s, f.readlines())
    config = parse_config(yml)
    print config
