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
en = enumerate
#h = lambda: _status = True
with open('meta.yml', 'r') as f:
    yml = map(s, f.readlines())
    config = d([(pth, d([(sp(ln)[0], sp(ln)[1]) for ln in yml[i + 1:] if s(ln) and q() and ((not e(ln)) or h())])) for i, pth in en(yml) if s(pth) and e(pth, ':') and c()])



