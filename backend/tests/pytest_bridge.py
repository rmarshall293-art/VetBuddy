"""Run pytest-style test modules under the stdlib unittest runner.

The Benefit Vault tests (backend/tests/vault) were written for pytest: plain
``assert``, fixtures as function arguments, ``pytest.raises`` and
``pytest.mark.parametrize``. This build has no package registry (ADR 0002), so
pytest is not installed and the repository's runner is ``unittest``. This
module keeps those tests as written:

* ``install()`` registers a small ``pytest`` stand-in module, but only when the
  real pytest cannot be imported. With pytest installed the same files run
  under pytest unchanged.
* ``suite_for(package)`` collects ``test_*`` functions from the package's
  ``test_*.py`` modules into a unittest suite, expanding parametrize marks and
  resolving fixtures (``conftest.py`` and the module's own) with session,
  module and function scope, including yield fixtures and their teardown.

Supported: fixture(scope=...), mark.parametrize (stacked), raises(exc,
match=...), skip, fail, importorskip, and the built-in fixtures tmp_path and
monkeypatch (setattr, setitem, setenv, delenv, delitem). Anything else raises
at collection time rather than being silently ignored.
"""
from __future__ import annotations

import atexit
import importlib
import importlib.util
import inspect
import itertools
import os
import re
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

# ── the stand-in pytest module ───────────────────────────────────────────────

_MISSING = object()


class _Fixture:
    def __init__(self, fn, scope: str):
        if scope not in ("function", "module", "session"):
            raise ValueError(f"unsupported fixture scope {scope}")
        self.fn, self.scope, self.name = fn, scope, fn.__name__


def fixture(fn=None, *, scope: str = "function", **unsupported):
    if unsupported:
        raise TypeError(f"pytest_bridge.fixture does not support {sorted(unsupported)}")

    def wrap(f):
        return _Fixture(f, scope)
    return wrap(fn) if fn is not None else wrap


class _Mark:
    @staticmethod
    def parametrize(argnames, argvalues, ids=None, **unsupported):
        if unsupported:
            raise TypeError(f"parametrize does not support {sorted(unsupported)}")
        names = [n.strip() for n in argnames.split(",")] if isinstance(argnames, str) else list(argnames)
        values = [v if len(names) > 1 else (v,) for v in argvalues]

        def wrap(fn):
            fn.__dict__.setdefault("_bridge_params", []).insert(0, (names, values))
            return fn
        return wrap

    def __getattr__(self, name):
        raise AttributeError(f"pytest.mark.{name} is not supported by pytest_bridge")


class _ExcInfo:
    value = None
    type = None


class _Raises:
    def __init__(self, expected, match=None):
        self.expected, self.match, self.info = expected, match, _ExcInfo()

    def __enter__(self):
        return self.info

    def __exit__(self, et, ev, tb):
        if et is None:
            raise AssertionError(f"DID NOT RAISE {self.expected}")
        if not issubclass(et, self.expected):
            return False
        if self.match is not None and not re.search(self.match, str(ev)):
            raise AssertionError(f"pattern {self.match!r} not found in {str(ev)!r}")
        self.info.value, self.info.type = ev, et
        return True


def raises(expected, *args, match=None, **kwargs):
    if args:   # pytest.raises(Exc, fn, *args) form
        with _Raises(expected, match) as info:
            args[0](*args[1:], **kwargs)
        return info
    return _Raises(expected, match)


def skip(reason: str = "", **_):
    raise unittest.SkipTest(reason)


def fail(reason: str = "", pytrace: bool = True):
    raise AssertionError(reason)


def importorskip(modname: str, minversion=None, reason=None):
    try:
        return importlib.import_module(modname)
    except ImportError:
        raise unittest.SkipTest(reason or f"could not import {modname!r}") from None


def install() -> bool:
    """Register the stand-in as ``pytest`` unless the real one is importable."""
    if "pytest" in sys.modules:
        return getattr(sys.modules["pytest"], "__bridge__", False)
    if importlib.util.find_spec("pytest") is not None:
        return False
    mod = types.ModuleType("pytest")
    mod.__bridge__ = True
    mod.fixture, mod.mark, mod.raises = fixture, _Mark(), raises
    mod.skip, mod.fail, mod.importorskip = skip, fail, importorskip
    sys.modules["pytest"] = mod
    return True


# ── built-in fixtures ────────────────────────────────────────────────────────

class _MonkeyPatch:
    def __init__(self):
        self._undo = []

    def setattr(self, target, name, value, raising=True):
        old = getattr(target, name, _MISSING)
        if old is _MISSING and raising:
            raise AttributeError(name)
        setattr(target, name, value)
        self._undo.append(lambda: delattr(target, name) if old is _MISSING else setattr(target, name, old))

    def setitem(self, mapping, key, value):
        old = mapping.get(key, _MISSING)
        mapping[key] = value
        self._undo.append(lambda: mapping.pop(key, None) if old is _MISSING else mapping.__setitem__(key, old))

    def delitem(self, mapping, key, raising=True):
        if key not in mapping:
            if raising:
                raise KeyError(key)
            return
        old = mapping.pop(key)
        self._undo.append(lambda: mapping.__setitem__(key, old))

    def setenv(self, name, value, prepend=None):
        self.setitem(os.environ, name, str(value))

    def delenv(self, name, raising=True):
        self.delitem(os.environ, name, raising)

    def undo(self):
        while self._undo:
            self._undo.pop()()


def _tmp_path():
    path = Path(tempfile.mkdtemp(prefix="vb-test-"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


def _monkeypatch():
    mp = _MonkeyPatch()
    yield mp
    mp.undo()


BUILTINS = {"tmp_path": _Fixture(_tmp_path, "function"), "monkeypatch": _Fixture(_monkeypatch, "function")}


# ── fixture resolution ───────────────────────────────────────────────────────

class _Scope:
    """Values and teardowns for one scope instance."""

    def __init__(self):
        self.values, self.finalizers = {}, []

    def close(self):
        errors = []
        while self.finalizers:
            try:
                self.finalizers.pop()()
            except BaseException as exc:   # keep tearing down
                errors.append(exc)
        self.values.clear()
        if errors:
            raise errors[0]


_SESSION = _Scope()
atexit.register(_SESSION.close)
_ORDER = {"function": 0, "module": 1, "session": 2}


class _Resolver:
    def __init__(self, registry: dict, module_scope: _Scope):
        self.registry, self.module_scope = registry, module_scope

    def get(self, name: str, fn_scope: _Scope, requester_scope: str = "function"):
        fx = self.registry.get(name) or BUILTINS.get(name)
        if fx is None:
            raise LookupError(f"fixture {name!r} not found")
        if _ORDER[fx.scope] < _ORDER[requester_scope]:
            raise LookupError(f"{requester_scope}-scoped fixture cannot use {fx.scope}-scoped {name!r}")
        scope = {"function": fn_scope, "module": self.module_scope, "session": _SESSION}[fx.scope]
        key = (id(fx), name)
        if key in scope.values:
            return scope.values[key]
        args = {p: self.get(p, fn_scope, fx.scope) for p in inspect.signature(fx.fn).parameters}
        result = fx.fn(**args)
        if inspect.isgenerator(result):
            gen = result
            value = next(gen)

            def finish(gen=gen):
                try:
                    next(gen)
                except StopIteration:
                    return
                raise RuntimeError(f"fixture {name!r} yielded twice")
            scope.finalizers.append(finish)
        else:
            value = result
        scope.values[key] = value
        return value


def _fixtures_in(module) -> dict:
    return {v.name: v for v in vars(module).values() if isinstance(v, _Fixture)}


class _ModuleSuite(unittest.TestSuite):
    """Runs a module's tests, then tears down its module-scoped fixtures."""

    def __init__(self, tests, scope: _Scope):
        super().__init__(tests)
        self._scope = scope

    def run(self, result, debug=False):
        try:
            return super().run(result, debug)
        finally:
            self._scope.close()


class _BridgedCase(unittest.FunctionTestCase):
    """Reports as module::test so runner output and failures name the test."""

    def __init__(self, fn, test_id: str, label: str):
        super().__init__(fn, description=label)
        self._test_id, self._label = test_id, label

    def id(self):
        return self._test_id

    def __str__(self):
        return self._label

    def shortDescription(self):
        return None


def _case(module_name: str, test_name: str, fn, resolver: _Resolver, bound: dict):
    def run():
        fn_scope = _Scope()
        try:
            args = {}
            for p in inspect.signature(fn).parameters:
                args[p] = bound[p] if p in bound else resolver.get(p, fn_scope)
            fn(**args)
        finally:
            fn_scope.close()
    run.__name__ = run.__qualname__ = test_name
    return _BridgedCase(run, f"{module_name}.{test_name}", f"{module_name}::{test_name}")


def _expand(fn):
    marks = getattr(fn, "_bridge_params", [])
    if not marks:
        yield fn.__name__, {}
        return
    for combo in itertools.product(*[list(enumerate(values)) for _, values in marks]):
        bound, ids = {}, []
        for (names, _), (i, vals) in zip(marks, combo):
            bound.update(zip(names, vals))
            ids.append(str(i))
        yield f"{fn.__name__}[{'-'.join(ids)}]", bound


def suite_for(package: str, package_dir: Path, pattern: str = "test_*.py") -> unittest.TestSuite:
    install()
    suite = unittest.TestSuite()
    conftest = importlib.import_module(f"{package}.conftest") if (package_dir / "conftest.py").exists() else None
    shared = _fixtures_in(conftest) if conftest else {}
    for path in sorted(package_dir.glob(pattern)):
        name = f"{package}.{path.stem}"
        try:
            module = importlib.import_module(name)
        except unittest.SkipTest as exc:
            suite.addTest(unittest.FunctionTestCase(lambda e=exc: (_ for _ in ()).throw(unittest.SkipTest(str(e))),
                                                    description=f"{name} (skipped: {exc})"))
            continue
        registry = {**shared, **_fixtures_in(module)}
        module_scope = _Scope()
        resolver = _Resolver(registry, module_scope)
        cases = []
        for attr, fn in vars(module).items():
            if attr.startswith("test_") and inspect.isfunction(fn) and fn.__module__ == module.__name__:
                for test_name, bound in _expand(fn):
                    cases.append(_case(name, test_name, fn, resolver, bound))
        suite.addTest(_ModuleSuite(cases, module_scope))
    return suite
