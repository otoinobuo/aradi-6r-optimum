class _ZZ:
    def __call__(self, x): return int(x)
    def __contains__(self, x): return isinstance(x, int)
ZZ = _ZZ()
def IntegerRing(): return ZZ
