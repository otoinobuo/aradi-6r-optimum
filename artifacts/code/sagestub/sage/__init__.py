# Auto-stub: any sage.* submodule not provided explicitly is created lazily with dummy attributes.
import sys, importlib.abc, importlib.machinery, types, os
_HERE = os.path.dirname(__file__)
class _Dummy:
    def __init__(self, name): self._name = name
    def __call__(self, *a, **k): raise NotImplementedError(f"sage stub: {self._name}")
    def __getattr__(self, n): return _Dummy(f"{self._name}.{n}")
class _StubModule(types.ModuleType):
    def __getattr__(self, n):
        if n.startswith("__"): raise AttributeError(n)
        return _Dummy(f"{self.__name__}.{n}")
class _Finder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, name, path, target=None):
        if not name.startswith("sage."): return None
        rel = os.path.join(_HERE, *name.split(".")[1:])
        if os.path.exists(rel + ".py") or os.path.isdir(rel): return None  # real stub file exists
        return importlib.machinery.ModuleSpec(name, self, is_package=True)
    def create_module(self, spec):
        m = _StubModule(spec.name); m.__path__ = []; return m
    def exec_module(self, module): pass
sys.meta_path.append(_Finder())
