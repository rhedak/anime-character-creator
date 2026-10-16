"""Function-level oracle: record REAL calls of every module-level function while rendering a corpus.

The whole-document oracle (manifest*.py) hashes the 53 part slots. It cannot test a shared
helper on its own, because a helper has no stage until a root part that uses it is ported.
This script records, for every `def` of character.py, skeleton.py, colorutil.py, presets.py and
urlstate.py (and the methods and properties of the dataclasses defined there, dunders
excluded), the arguments and the result of real calls. The TypeScript side decodes a recorded
call, calls the same-named function and compares the result. See docs/ts-port-calls.md.

    PY=/Users/hanssen.henrik/git/self-study/anime-character-creator-dev/.venv/bin/python
    PYTHONDONTWRITEBYTECODE=1 $PY harness/ts_port/calls.py record [--corpus wide,full] [--limit N] [--out SCRATCH_DIR]
    PYTHONDONTWRITEBYTECODE=1 $PY harness/ts_port/calls.py check  [--limit N]
    PYTHONDONTWRITEBYTECODE=1 $PY harness/ts_port/calls.py selftest
    PYTHONDONTWRITEBYTECODE=1 $PY harness/ts_port/calls.py replay [--dir out|fixtures]   # decode and re-call, plain process
    PYTHONDONTWRITEBYTECODE=1 $PY harness/ts_port/calls.py list-uncalled
    PYTHONDONTWRITEBYTECODE=1 $PY harness/ts_port/calls.py sample      # rebuild fixtures/calls from out/calls
    PYTHONDONTWRITEBYTECODE=1 $PY harness/ts_port/calls.py doc         # refresh the tables in docs/ts-port-calls.md

Mechanism. An AST import hook (no .pyc read or written, like instrument.py) appends, after each
module-level `def f` of the five target modules, `f = __cw(f, __name__)`, and after each
module-level class `__cwc(Cls, __name__)`. `__cw` returns a recording wrapper; `__cwc` replaces
the methods and properties of the class by wrappers. Because the name is rebound inside the
module, every later use is a wrapper: internal calls (a global lookup at call time), `from .x
import f` in another module, and functions stored in module-level tables. Calls made while the
package imports (module constants built by calling helpers) and while the corpus code builds a
case (`Expression.applied_to`, `replace`, validators) are recorded too, and counted separately
(`calls_by_phase`: import, build, drive). The wrapper returns exactly what the function returns and re-raises
its exception unchanged.

Dedupe. A call is keyed by a fast structural key (floats by their IEEE bits, so 0.0 and -0.0
differ, and 1 and 1.0 differ) and its 64-bit hash goes in a per-function dict. That key tells
calls apart exactly as the sha256 of the canonical JSON of (args, kwargs) does (the registry
ref name is part of the key); `record` asserts the sha256 of every kept call is unique.

Value encoding (JSON, exact, decodable in TypeScript):
  float -> "f:" + 16 hex digits of the big-endian IEEE-754 bits   int -> "i:" + decimal
  bool -> "b:1" / "b:0"      str -> "s:" + text      None -> null
  tuple -> {"t": [...]}      list -> {"l": [...]}    dict -> {"d": [[key, value], ...]} (insertion order)
  set / frozenset -> {"set": [...]} sorted by the JSON text of the encoded members
  dataclass -> {"dc": "ClassName", "f": {field: value, ...}} in field order
  an object that IS (identity) a registered module-level constant -> {"ref": "HAIRSTYLES.long_blunt"}
  exception -> result {"exc": "ClassName", "msg": "..."}
A call with a function, class or other un-encodable value as an argument, or a callable or lazy
result, is counted as unrecordable and not kept.
"""

from __future__ import annotations

import ast
import builtins
import collections
import collections.abc
import dataclasses
import functools
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import inspect
import json
import math
import os
import random
import re
import struct
import subprocess
import sys
import time
import types
import zlib
from pathlib import Path
from typing import Any

import _bootstrap

HERE = _bootstrap.HERE
WORKTREE = _bootstrap.WORKTREE
OUT = HERE / "out" / "calls"
FIXTURES = HERE / "fixtures" / "calls"
DOCS = HERE / "docs" / "ts-port-calls.md"
TARGETS = (
    "anime_character_creator.character",
    "anime_character_creator.skeleton",
    "anime_character_creator.colorutil",
    "anime_character_creator.presets",
    "anime_character_creator.urlstate",
)
SHORT = {m: m.rsplit(".", 1)[1] for m in TARGETS}

SEED = 20261016
FIRST_N = 40  # the first distinct calls of a function, always kept
SAMPLE_N = 40  # then a reservoir over the rest of the distinct calls
RAISE_CAP = 1000  # distinct raising calls kept per function
MAX_PATHS = 160  # float argument positions tracked per function for the extremes
SPECIAL_CAP = 3  # nan / inf / -0.0 calls kept per kind and function
MAX_BYTES = 200_000  # a call larger than this (args + kwargs + result, JSON) is skipped
FIX_MAX_CALLS = 12
FIX_MAX_BYTES = 60_000
FIX_TOTAL_BYTES = 3_000_000

_pack = struct.Struct(">d").pack

# --------------------------------------------------------------------------
# state shared by the wrappers
# --------------------------------------------------------------------------
RUN = [False]  # recording on (the corpus loaders switch it off while they build cases)
RUN_ON = [True]  # False in the plain (check) pass: the same loop with no recording
PHASE = [0]  # 0 while the package imports, 1 while a corpus builds the next case, 2 while a case is driven
MUT = [False]  # the last key computation met a mutable container
REFS: dict[int, str] = {}  # id(object) -> registry name, filled after the import
REG_OBJS: dict[str, Any] = {}  # registry name -> the object (keeps it alive)
UNREGISTERED: dict[str, str] = {}  # module-level containers left out of the registry, with the reason
RECS: list[Rec] = []
_DCC: dict[int, tuple[Any, Any]] = {}  # id(frozen dataclass) -> (object, key); cleared per case
DCINFO: dict[type, Any] = {}
BUDGET = [MAX_BYTES]
FN_OK = [False]  # True while the registry is encoded: a package function becomes {"fn": "module.name"}


class Unencodable(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class TooLarge(Exception):
    pass


class _Sentinel:
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name


TRUE, FALSE, NONE = _Sentinel("T"), _Sentinel("F"), _Sentinel("N")
LST, DCT, SETK, DCK, REFK = (_Sentinel(n) for n in ("L", "D", "S", "C", "R"))
MISS = object()
LARGE = 2  # a value in Rec.seen; the others: an entry dict (kept), 0 (distinct, not kept), a str (unrecordable: the reason)

LAZY = (
    types.GeneratorType,
    map,
    filter,
    zip,
    enumerate,
    reversed,
    range,
    type({}.keys()),
    type({}.values()),
    type({}.items()),
    collections.abc.Iterator,
)


def _dcinfo(t: type) -> Any:
    f = getattr(t, "__dataclass_fields__", None)
    if f is None:
        DCINFO[t] = False
        return False
    params = getattr(t, "__dataclass_params__", None)
    DCINFO[t] = (tuple(x.name for x in dataclasses.fields(t)), bool(params and params.frozen))
    return DCINFO[t]


# --------------------------------------------------------------------------
# key (fast, exact) and encoding (JSON)
# --------------------------------------------------------------------------
def K(v: Any) -> Any:
    """A hashable key that tells values apart exactly as the JSON encoding does."""
    t = type(v)
    if t is float:
        return _pack(v)
    if t is int or t is str:
        return v
    if t is tuple:
        r = REFS.get(id(v))
        if r is not None:
            return (REFK, r)
        return tuple([K(x) for x in v])
    if t is bool:
        return TRUE if v else FALSE
    if v is None:
        return NONE
    if t is list:
        r = REFS.get(id(v))
        if r is not None:
            return (REFK, r)
        MUT[0] = True
        return (LST, *[K(x) for x in v])
    if t is dict:
        r = REFS.get(id(v))
        if r is not None:
            return (REFK, r)
        MUT[0] = True
        return (DCT, *[(K(a), K(b)) for a, b in v.items()])
    info = DCINFO.get(t)
    if info is None:
        info = _dcinfo(t)
    if info:
        r = REFS.get(id(v))
        if r is not None:
            return (REFK, r)
        names, frozen = info
        if frozen:
            c = _DCC.get(id(v))
            if c is not None and c[0] is v:
                return c[1]
        else:
            MUT[0] = True
        key = (DCK, t, *[K(getattr(v, n)) for n in names])
        if frozen:
            _DCC[id(v)] = (v, key)
        return key
    if t is set or t is frozenset:
        r = REFS.get(id(v))
        if r is not None:
            return (REFK, r)
        if t is set:
            MUT[0] = True
        return (SETK, t is set, frozenset([K(x) for x in v]))
    if callable(v):
        raise Unencodable("callable argument (" + t.__name__ + ")")
    raise Unencodable("type " + t.__name__)


def _spend(n: int) -> None:
    BUDGET[0] -= n
    if BUDGET[0] < 0:
        raise TooLarge


def enc(v: Any) -> Any:
    t = type(v)
    if t is float:
        _spend(24)
        return "f:" + _pack(v).hex()
    if t is int:
        _spend(12)
        return "i:" + str(v)
    if t is str:
        _spend(len(v) + 4)
        return "s:" + v
    if t is bool:
        _spend(6)
        return "b:1" if v else "b:0"
    if v is None:
        _spend(4)
        return None
    _spend(8)
    info = DCINFO.get(t)
    if info is None:
        info = _dcinfo(t)
    if t is tuple or t is list or t is dict or t is set or t is frozenset or info:
        r = REFS.get(id(v))
        if r is not None:
            return {"ref": r}
    if t is tuple:
        return {"t": [enc(x) for x in v]}
    if t is list:
        return {"l": [enc(x) for x in v]}
    if t is dict:
        return {"d": [[enc(a), enc(b)] for a, b in v.items()]}
    if t is set or t is frozenset:
        out = {"set": sorted([enc(x) for x in v], key=lambda e: json.dumps(e, separators=(",", ":")))}
        if t is frozenset:
            out["frozen"] = True
        return out
    if info:
        return {"dc": t.__name__, "f": {n: enc(getattr(v, n)) for n in info[0]}}
    if FN_OK[0] and isinstance(v, types.FunctionType):
        return {"fn": v.__module__.rsplit(".", 1)[-1] + "." + v.__qualname__}
    if callable(v):
        raise Unencodable("callable (" + t.__name__ + ")")
    raise Unencodable("type " + t.__name__)


def dumps(o: Any) -> str:
    return json.dumps(o, separators=(",", ":"), ensure_ascii=True)


def sha_of(args: Any, kwargs: Any) -> str:
    return hashlib.sha256(dumps([args, kwargs]).encode("ascii")).hexdigest()


def dec_float(s: str) -> float:
    return struct.unpack(">d", bytes.fromhex(s[2:]))[0]


# --------------------------------------------------------------------------
# float positions (for the extremes)
# --------------------------------------------------------------------------
def _walk(v: Any, path: tuple, depth: int, out: list) -> None:
    t = type(v)
    if t is float:
        out.append((path, v))
    elif depth < 3:
        if t is tuple or t is list:
            if len(v) <= 64 and id(v) not in REFS:
                for i, x in enumerate(v):
                    _walk(x, (*path, i), depth + 1, out)
        elif t is dict:
            if len(v) <= 64 and id(v) not in REFS:
                for kk, x in v.items():
                    if type(kk) is str:
                        _walk(x, (*path, "[" + kk + "]"), depth + 1, out)
        else:
            info = DCINFO.get(t)
            if info is None:
                info = _dcinfo(t)
            if info and id(v) not in REFS:
                for n in info[0]:
                    _walk(getattr(v, n), (*path, "." + n), depth + 1, out)


def floats_of(args: tuple, kwargs: dict) -> list:
    out: list = []
    for i, a in enumerate(args):
        _walk(a, (i,), 0, out)
    for n, v in kwargs.items():
        _walk(v, ("k:" + n,), 0, out)
    return out


def path_str(path: tuple) -> str:
    s = ""
    for j, p in enumerate(path):
        if j == 0:
            s += ("a%d" % p) if isinstance(p, int) else p
        elif isinstance(p, int):
            s += "[%d]" % p
        else:
            s += p
    return s


# --------------------------------------------------------------------------
# per-function record
# --------------------------------------------------------------------------
class Rec:
    __slots__ = (
        "name", "module", "line", "fn", "total", "by_phase", "distinct", "seen", "unrec", "unrec_reasons",
        "large", "large_examples", "raised", "mutated", "mutated_example", "lazy", "lazy_types", "rng", "slots",
        "entries", "ext", "special", "raises_kept", "kind",
    )  # fmt: skip

    def __init__(self, name: str, module: str, fn: Any, kind: str) -> None:
        self.name = name
        self.module = module
        self.fn = fn
        self.kind = kind
        code = getattr(fn, "__code__", None)
        self.line = code.co_firstlineno if code else 0
        self.total = 0
        self.by_phase = [0, 0, 0]
        self.distinct = 0
        self.seen: dict[int, Any] = {}
        self.unrec = 0
        self.unrec_reasons: collections.Counter[str] = collections.Counter()
        self.large = 0
        self.large_examples: list[str] = []
        self.raised = 0
        self.mutated = 0
        self.mutated_example: Any = None
        self.lazy = 0
        self.lazy_types: collections.Counter[str] = collections.Counter()
        self.rng = random.Random(SEED ^ zlib.crc32((module + "." + name).encode()))
        self.slots: list[Any] = []
        self.entries: list[dict] = []
        self.ext: dict[tuple, list] = {}
        self.special: collections.Counter[str] = collections.Counter()
        self.raises_kept = 0


def _drop(e: dict) -> None:
    e["dead"] = True
    e["args"] = e["kwargs"] = e["result"] = None


def _lose(e: dict, tag: str) -> None:
    e["why"].discard(tag)
    if not e["why"]:
        _drop(e)


def _make_entry(rec: Rec, args: tuple, kwargs: dict, seq: int) -> dict:
    BUDGET[0] = MAX_BYTES
    ea = [enc(a) for a in args]
    ek = {n: enc(kwargs[n]) for n in sorted(kwargs)}
    e = {"args": ea, "kwargs": ek, "result": None, "count": 1, "why": set(), "seq": seq}
    rec.entries.append(e)
    return e


def _set_result(e: dict, res: Any) -> None:
    BUDGET[0] = MAX_BYTES
    e["result"] = enc(res)
    if len(dumps([e["args"], e["kwargs"], e["result"]])) > MAX_BYTES:
        raise TooLarge


def _note_unrec(rec: Rec, reason: str) -> None:
    rec.unrec += 1
    rec.unrec_reasons[reason] += 1


def _kill(rec: Rec, e: dict) -> None:
    _drop(e)
    for st in rec.ext.values():
        if st[2] is e:
            st[2] = None
        if st[3] is e:
            st[3] = None


def _first_sight(rec: Rec, fn: Any, args: tuple, kwargs: dict, k: Any, h: int, mut: bool) -> Any:
    """A call never seen before: decide whether to keep it, make the call, record the outcome."""
    seen = rec.seen
    seen[h] = 0
    j = rec.distinct
    rec.distinct = j + 1
    why: list[str] = []
    slot = None
    if j < FIRST_N:
        why.append("first")
    else:
        m = j - FIRST_N + 1
        if m <= SAMPLE_N:
            slot = len(rec.slots)
        else:
            r = rec.rng.randrange(m)
            if r < SAMPLE_N:
                slot = r
        if slot is not None:
            why.append("sample")
    # extremes and special floats of this call
    upd: list[tuple[tuple, str, list | None]] = []  # (path, "new" | "min" | "max", tracker)
    special: list[str] = []
    ext = rec.ext
    n_new = 0
    for path, v in floats_of(args, kwargs):
        if v != v:
            kind = "nan"
        elif v == math.inf or v == -math.inf:
            kind = "inf"
        elif v == 0.0 and math.copysign(1.0, v) < 0:
            kind = "negzero"
        else:
            kind = ""
        if kind:
            if rec.special[kind] + special.count(kind) < SPECIAL_CAP:
                special.append(kind)
            if kind == "nan":
                continue
        st = ext.get(path)
        if st is None:
            if len(ext) + n_new < MAX_PATHS:
                n_new += 1
                upd.append((path, "new", None))
        elif v < st[0]:
            upd.append((path, "min", st))
        elif v > st[1]:
            upd.append((path, "max", st))
    entry = None
    if why or upd or special:
        try:
            entry = _make_entry(rec, args, kwargs, j)
        except TooLarge:
            rec.large += 1
            seen[h] = LARGE
            if len(rec.large_examples) < 3:
                rec.large_examples.append("arguments over %d bytes" % MAX_BYTES)
            return fn(*args, **kwargs)
        except Unencodable as u:
            _note_unrec(rec, u.reason)
            seen[h] = u.reason
            return fn(*args, **kwargs)
        if "first" in why:
            entry["why"].add("first")
        if slot is not None:
            if slot == len(rec.slots):
                rec.slots.append(entry)
            else:
                _lose(rec.slots[slot], "sample")
                rec.slots[slot] = entry
            entry["why"].add("sample")
        for kind in special:
            rec.special[kind] += 1
            entry["why"].add("special:" + kind)
        floats = None
        for path, which, st in upd:
            ps = path_str(path)
            if which == "new":
                v = next(x for p, x in floats_of(args, kwargs) if p == path) if floats is None else floats[path]
                ext[path] = [v, v, entry, entry]
                entry["why"].add("min:" + ps)
                entry["why"].add("max:" + ps)
                continue
            v = next(x for p, x in floats_of(args, kwargs) if p == path)
            idx = 2 if which == "min" else 3
            if st[idx] is not None:
                _lose(st[idx], which + ":" + ps)
            st[0 if which == "min" else 1] = v
            st[idx] = entry
            entry["why"].add(which + ":" + ps)
    try:
        res = fn(*args, **kwargs)
    except Exception as ex:
        rec.raised += 1
        e = entry
        if e is None and rec.raises_kept < RAISE_CAP:
            try:
                e = _make_entry(rec, args, kwargs, j)
            except (TooLarge, Unencodable):
                e = None
        if e is not None:
            if "raises" not in e["why"]:
                rec.raises_kept += 1
            e["why"].add("raises")
            e["result"] = {"exc": type(ex).__name__, "msg": str(ex)}
            seen[h] = e
        raise
    if mut:
        try:
            k2 = (tuple([K(a) for a in args]), tuple([(n, K(kwargs[n])) for n in sorted(kwargs)]) if kwargs else ())
        except Unencodable:
            k2 = None
        if k2 != k:
            rec.mutated += 1
            if rec.mutated_example is None:
                rec.mutated_example = {"call_index": j}
    if isinstance(res, LAZY):
        rec.lazy += 1
        rec.lazy_types[type(res).__name__] += 1
        reason = "lazy result (" + type(res).__name__ + ")"
        _note_unrec(rec, reason)
        seen[h] = reason
        if entry is not None:
            _kill(rec, entry)
        return res
    if callable(res):
        reason = "callable result (" + type(res).__name__ + ")"
        _note_unrec(rec, reason)
        seen[h] = reason
        if entry is not None:
            _kill(rec, entry)
        return res
    if entry is not None:
        try:
            _set_result(entry, res)
        except TooLarge:
            rec.large += 1
            if len(rec.large_examples) < 3:
                rec.large_examples.append("call over %d bytes (result type %s)" % (MAX_BYTES, type(res).__name__))
            seen[h] = LARGE
            _kill(rec, entry)
        except Unencodable as u:
            _note_unrec(rec, "result: " + u.reason)
            seen[h] = "result: " + u.reason
            _kill(rec, entry)
        else:
            seen[h] = entry
    return res


def make_wrapper(fn: Any, name: str, modname: str, kind: str = "function") -> Any:
    rec = Rec(name, modname, fn, kind)
    RECS.append(rec)
    seen = rec.seen

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not RUN[0]:
            return fn(*args, **kwargs)
        rec.total += 1
        rec.by_phase[PHASE[0]] += 1
        MUT[0] = False
        try:
            k = (tuple([K(a) for a in args]), tuple([(n, K(kwargs[n])) for n in sorted(kwargs)]) if kwargs else ())
        except Unencodable as u:
            rec.unrec += 1
            rec.unrec_reasons[u.reason] += 1
            return fn(*args, **kwargs)
        h = hash(k)
        e = seen.get(h, MISS)
        if e is MISS:
            return _first_sight(rec, fn, args, kwargs, k, h, MUT[0])
        if e.__class__ is dict:
            e["count"] += 1
        elif e.__class__ is str:
            rec.unrec += 1
            rec.unrec_reasons[e] += 1
        elif e == LARGE:
            rec.large += 1
        return fn(*args, **kwargs)

    return wrapper


def func_wrapper(fn: Any, modname: str) -> Any:
    """What `f = __cw(f, __name__)` calls: wrap a module-level function under its own name."""
    return make_wrapper(fn, fn.__name__, modname)


def class_wrapper(cls: type, modname: str) -> type:
    for attr, v in list(vars(cls).items()):
        if attr.startswith("__") and attr.endswith("__"):
            continue
        name = cls.__name__ + "." + attr
        if isinstance(v, types.FunctionType):
            setattr(cls, attr, make_wrapper(v, name, modname, "method"))
        elif isinstance(v, property) and v.fget is not None:
            setattr(cls, attr, property(make_wrapper(v.fget, name, modname, "property"), v.fset, v.fdel, v.__doc__))
        elif isinstance(v, (staticmethod, classmethod)):
            setattr(cls, attr, type(v)(make_wrapper(v.__func__, name, modname, "method")))
    return cls


# --------------------------------------------------------------------------
# import hook
# --------------------------------------------------------------------------
def transform(source: str, path: str) -> ast.Module:
    tree = ast.parse(source, path)
    body: list[ast.stmt] = []
    for st in tree.body:
        body.append(st)
        if isinstance(st, ast.FunctionDef):
            extra = ast.parse(f"{st.name} = __cw({st.name}, __name__)").body[0]
        elif isinstance(st, ast.ClassDef):
            extra = ast.parse(f"__cwc({st.name}, __name__)").body[0]
        else:
            continue
        for n in ast.walk(extra):
            ast.copy_location(n, st)
        body.append(extra)
    tree.body = body
    ast.fix_missing_locations(tree)
    return tree


class RecordingLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname: str) -> Any:
        path = self.get_filename(fullname)
        return compile(transform(self.get_data(path).decode("utf-8"), path), path, "exec", dont_inherit=True)


class RecordingFinder(importlib.abc.MetaPathFinder):
    def __init__(self, targets: tuple[str, ...]) -> None:
        self.targets = targets

    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> Any:
        if fullname not in self.targets:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.origin is None:
            return None
        return importlib.util.spec_from_file_location(fullname, spec.origin, loader=RecordingLoader(fullname, spec.origin))


def install_hook(targets: tuple[str, ...] = TARGETS) -> None:
    if "anime_character_creator" in sys.modules:
        raise RuntimeError("anime_character_creator already imported; install_hook() must come first")
    sys.dont_write_bytecode = True
    builtins.__cw = func_wrapper  # type: ignore[attr-defined]
    builtins.__cwc = class_wrapper  # type: ignore[attr-defined]
    sys.meta_path.insert(0, RecordingFinder(targets))
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 3000))  # a wrapper doubles the Python frames of a call
    RUN[0] = True
    PHASE[0] = 0
    _bootstrap.assert_package_location()
    import anime_character_creator  # noqa: F401

    for m in targets:
        importlib.import_module(m)  # urlstate is not imported by the package
        if not isinstance(sys.modules[m].__loader__, RecordingLoader):
            raise RuntimeError(f"{m} was not loaded by the recording loader")
    PHASE[0] = 2
    RUN[0] = False


# --------------------------------------------------------------------------
# registry of module-level constants (identity -> name)
# --------------------------------------------------------------------------
COMPOUND = (dict, list, tuple, set, frozenset)


def _is_compound(v: Any) -> bool:
    if isinstance(v, COMPOUND):
        return len(v) > 0
    return bool(DCINFO.get(type(v)) or _dcinfo(type(v)))


def build_registry() -> dict[str, dict[str, Any]]:
    """Fill REFS by scanning module globals of the target modules. Returns name -> info."""
    REFS.clear()
    REG_OBJS.clear()
    reg: dict[str, dict[str, Any]] = {}

    def add(name: str, module: str, v: Any, level: int) -> None:
        if id(v) in REFS:
            return
        if name in REG_OBJS:
            name = f"{module}.{name}"
            if name in REG_OBJS:
                return
        REFS[id(v)] = name
        REG_OBJS[name] = v
        reg[name] = {"module": module, "level": level, "kind": type(v).__name__}

    mods = [sys.modules[m] for m in TARGETS]
    for m in mods:
        short = SHORT[m.__name__]
        for n, v in vars(m).items():
            if n.startswith("__") or isinstance(v, (types.FunctionType, types.ModuleType, type, types.GenericAlias)):
                continue
            if _is_compound(v):
                add(n, short, v, 0)
    for m in mods:
        short = SHORT[m.__name__]
        for n, v in vars(m).items():
            if n.startswith("__") or n not in REG_OBJS or REG_OBJS[n] is not v:
                continue
            if isinstance(v, dict):
                for key, x in v.items():
                    if _is_compound(x) and not isinstance(x, (set, frozenset)):
                        add(f"{n}.{key}" if isinstance(key, str) else f"{n}[{key!r}]", short, x, 1)
            elif isinstance(v, (list, tuple)):
                for i, x in enumerate(v):
                    if _is_compound(x) and (isinstance(x, dict) or DCINFO.get(type(x))):
                        add(f"{n}[{i}]", short, x, 1)
    for name in list(reg):
        try:
            reg[name]["value"] = _enc_by_value(REG_OBJS[name])
        except Unencodable as u:  # a table of functions, for instance: not a constant a call can carry
            UNREGISTERED[name] = u.reason
            REFS.pop(id(REG_OBJS.pop(name)))
            del reg[name]
    return reg


def _enc_by_value(v: Any) -> Any:
    """Encode `v` itself by value (its own ref switched off); its children keep their refs."""
    saved = REFS.pop(id(v), None)
    FN_OK[0] = True
    try:
        BUDGET[0] = 10**9
        return enc(v)
    finally:
        FN_OK[0] = False
        if saved is not None:
            REFS[id(v)] = saved


def registry_value_check(reg: dict[str, dict[str, Any]]) -> list[str]:
    """Names whose current value differs from the value at the start (a constant was mutated)."""
    return [name for name, info in reg.items() if dumps(_enc_by_value(REG_OBJS[name])) != dumps(info["value"])]


# --------------------------------------------------------------------------
# corpora
# --------------------------------------------------------------------------
def params_from_entry(entry: dict[str, Any], defaults: dict[str, Any]) -> Any:
    """Mirror of corpus_full.load_full_case: params as a diff from the defaults (`{"$float"}` for non-finite)."""
    import cases

    def dec(v: Any) -> Any:
        if isinstance(v, dict) and set(v) == {"$float"}:
            return float(v["$float"])
        return v

    full = {k: (dict(v) if isinstance(v, dict) else v) for k, v in defaults.items()}
    for k, v in entry["p"].items():
        if k in ("outfit", "face"):
            for kk, vv in v.items():
                if kk not in full[k]:
                    raise KeyError(f"{entry['id']}: unknown {k} field {kk!r}")
                full[k][kk] = dec(vv)
        else:
            if k not in full:
                raise KeyError(f"{entry['id']}: unknown field {k!r}")
            full[k] = dec(v)
    return cases.params_from_dict(full)


def _dec_obj(v: Any) -> Any:
    if isinstance(v, dict):
        if set(v) == {"$float"}:
            return float(v["$float"])
        return {k: _dec_obj(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_dec_obj(x) for x in v]
    return v


def iter_cases(corpora: list[str], limit: int):
    """Yield (id, kind, payload). kind "render": payload (params, kwargs); "url": payload (op, arg)."""
    import cases
    from anime_character_creator.character import CharacterParams

    n = 0
    for name in corpora:
        if name == "mini":
            for c in cases.load_cases():
                yield f"mini-{c['id']}", "render", (c["p"], dict(c["kwargs"]))
                n += 1
                if limit and n >= limit:
                    return
        elif name == "wide":
            import corpus_wide

            for i, p in enumerate(corpus_wide.corpus()):
                yield f"wide-{i}", "render", (p, {"id_prefix": ""})
                yield f"wide-{i}x", "render", (p, {"id_prefix": "x"})
                n += 1
                if limit and n >= limit:
                    return
        elif name == "full":
            defaults = dataclasses.asdict(CharacterParams())
            ok = json.loads((HERE / "corpus" / "full.json").read_text(encoding="utf-8"))
            for e in ok:
                yield f"full-{e['id']}", "render", (params_from_entry(e, defaults), dict(e["kw"]))
                n += 1
                if limit and n >= limit:
                    return
            errs = json.loads((HERE / "corpus" / "errors.json").read_text(encoding="utf-8"))
            for e in errs:
                if e["op"] == "render":
                    yield f"err-{e['id']}", "render", (params_from_entry(e, defaults), dict(e["kw"]))
                elif e["op"] == "params_from_dict":
                    yield f"err-{e['id']}", "url", ("params_from_dict", _dec_obj(e["arg"]))
                elif e["op"] == "decode_params":
                    yield f"err-{e['id']}", "url", ("decode_params", e["arg"])
                n += 1
                if limit and n >= limit:
                    return
        else:
            raise SystemExit(f"unknown corpus {name!r}")


def run_one(ch: Any, us: Any, cid: str, kind: str, payload: Any, hashes: list, urlstate_extras: bool, errs: collections.Counter) -> None:
    _DCC.clear()
    if kind == "url":
        op, arg = payload
        RUN[0] = RUN_ON[0]
        try:
            getattr(us, op)(arg)
        except Exception as e:  # data
            errs["url " + type(e).__name__] += 1
        finally:
            RUN[0] = False
        return
    p, kw = payload
    RUN[0] = RUN_ON[0]
    try:
        doc = ch.render_character(p, **kw)
        hashes.append([cid, hashlib.sha256(doc.encode()).hexdigest()])
    except Exception as e:  # data
        errs["render " + type(e).__name__] += 1
        hashes.append([cid, "EXC " + f"{type(e).__name__}: {str(e)[:120]}"])
    finally:
        RUN[0] = False
    if urlstate_extras and RUN_ON[0]:
        RUN[0] = True
        try:
            s = us.encode_params(p)
            us.decode_params(s)
            us.params_from_dict(us.params_to_dict(p))
            us.character_url(p, "https://example.com/app/")
        except Exception as e:  # data
            errs["urlstate " + type(e).__name__] += 1
        finally:
            RUN[0] = False


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------
def stem_map(recs: list[Rec]) -> dict[Rec, str]:
    """File stem per function: its name, or `module.name` when two modules define the same name."""
    count = collections.Counter(r.name for r in recs)
    return {r: (f"{SHORT[r.module]}.{r.name}" if count[r.name] > 1 else r.name) for r in recs}


def final_entries(rec: Rec) -> list[dict]:
    es = [e for e in rec.entries if not e.get("dead") and e["why"]]
    es.sort(key=lambda e: e["seq"])
    return es


def render_file(info: dict[str, Any], calls: list[dict]) -> str:
    head = dumps(info)[:-1]
    body = ",\n".join(dumps(c) for c in calls)
    return head + ',"calls":[\n' + body + ("\n" if calls else "") + "]}\n"


def call_json(e: dict) -> dict:
    return {"args": e["args"], "kwargs": e["kwargs"], "result": e["result"], "count": e["count"], "why": sorted(e["why"])}


def sig_of(fn: Any) -> str:
    try:
        return str(inspect.signature(fn))
    except (TypeError, ValueError):
        return "?"


def effective_recs(shadowed_out: list | None = None) -> list[Rec]:
    """One Rec per function as the modules end up: the later def wins when a name is defined twice."""
    by_key: dict[tuple[str, str], Rec] = {}
    for r in RECS:
        key = (r.module, r.name)
        if key in by_key and shadowed_out is not None:
            shadowed_out.append(by_key[key])
        by_key[key] = r
    return list(by_key.values())


def write_outputs(meta: dict[str, Any], reg: dict[str, Any]) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    shadowed: list[Rec] = []
    recs = effective_recs(shadowed)
    shadow_by_key = {(r.module, r.name): r for r in shadowed}
    stems = stem_map(recs)
    index = []
    for r in sorted(recs, key=lambda r: (r.module, r.line, r.name)):
        es = final_entries(r)
        shas = [sha_of(e["args"], e["kwargs"]) for e in es]
        if len(set(shas)) != len(shas):
            raise RuntimeError(f"{r.name}: two kept calls have the same sha256")
        info = {
            "function": r.name,
            "module": SHORT[r.module],
            "line": r.line,
            "kind": r.kind,
            "total_calls": r.total,
            "calls_by_phase": {"import": r.by_phase[0], "build": r.by_phase[1], "drive": r.by_phase[2]},
            "distinct": r.distinct,
            "unrecordable": r.unrec,
            "skipped_large": r.large,
            "raised_distinct": r.raised,
            "kept": len(es),
        }
        calls = [call_json(e) for e in es]
        (OUT / f"{stems[r]}.json").write_text(render_file(info, calls), encoding="utf-8")
        ix = dict(info)
        ix["stem"] = stems[r]
        ix["signature"] = sig_of(r.fn)
        ix["unrecordable_reasons"] = dict(r.unrec_reasons)
        ix["lazy_results"] = dict(r.lazy_types)
        ix["mutates_arguments"] = r.mutated
        ix["large_examples"] = r.large_examples
        ix["float_positions"] = len(r.ext)
        ix["kept_reasons"] = dict(collections.Counter(w.split(":")[0] for e in es for w in e["why"]))
        sh = shadow_by_key.get((r.module, r.name))
        if sh is not None:
            ix["shadowed_def"] = {"line": sh.line, "calls": sh.total, "note": "an earlier def of the same name, replaced by the one above"}
        index.append(ix)
    meta["pruned_stale_out_files"] = _prune(OUT, {f"{stem}.json" for stem in stems.values()} | {"_index.json", "_registry.json", "_wrapped_hashes.json"})
    (OUT / "_index.json").write_text(json.dumps({"meta": meta, "functions": index}, indent=1) + "\n", encoding="utf-8")
    (OUT / "_registry.json").write_text(json.dumps({"constants": reg}, separators=(",", ":")) + "\n", encoding="utf-8")
    return {"index": index, "stems": stems}


# --------------------------------------------------------------------------
# committed sample
# --------------------------------------------------------------------------
def pick_sample(calls: list[dict], max_calls: int, max_bytes: int) -> list[dict]:
    """Every raising call (up to half), the extremes (greedy cover of the min/max tags), a special, then a spread."""
    chosen: dict[int, dict] = {}

    def add(i: int) -> None:
        if len(chosen) < max_calls:
            chosen[i] = calls[i]

    def whys(i: int) -> set[str]:
        return set(calls[i]["why"])

    for i in range(len(calls)):
        if "raises" in whys(i) and sum(1 for c in chosen.values() if "raises" in c["why"]) < max_calls // 2:
            add(i)
    tags = {t for i in range(len(calls)) for t in whys(i) if t.startswith(("min:", "max:"))}
    covered: set[str] = set()
    budget_ext = max(max_calls - 3, 1)
    while tags - covered and len(chosen) < budget_ext:
        best = max(range(len(calls)), key=lambda i: (len((whys(i) & tags) - covered), -len(dumps(calls[i]))))
        gain = (whys(best) & tags) - covered
        if not gain:
            break
        covered |= gain
        add(best)
    for i in range(len(calls)):
        if any(t.startswith("special:") for t in whys(i)) and not any(t.startswith("special:") for c in chosen.values() for t in c["why"]):
            add(i)
    rest = [i for i in range(len(calls)) if i not in chosen]
    room = max_calls - len(chosen)
    if room > 0 and rest:
        step = len(rest) / room
        for j in range(min(room, len(rest))):
            add(rest[int(j * step)])
    keep = [chosen[i] for i in sorted(chosen)]
    while len(dumps(keep)) > max_bytes and len(keep) > 1:
        order = sorted(range(len(keep)), key=lambda i: ("raises" in keep[i]["why"], -len(dumps(keep[i]))))
        keep.pop(order[0])
    return keep


def _prune(directory: Path, keep: set[str]) -> int:
    """Delete the .json files of a previous run that this run did not write (os.unlink, never a shell rm)."""
    n = 0
    for f in directory.glob("*.json"):
        if f.name not in keep:
            f.unlink()
            n += 1
    return n


META_FILES = {"_index.json", "_registry.json", "_wrapped_hashes.json"}  # not one function's calls


# (max calls, max bytes) tried in this order until the call files fit FIX_CALLS_BUDGET
FIX_COMBOS = [(12, 60_000), (12, 40_000), (10, 30_000), (8, 30_000), (8, 20_000), (6, 20_000), (5, 20_000), (4, 20_000), (4, 15_000), (3, 15_000), (3, 14_000), (3, 12_000), (3, 10_000), (2, 10_000)]
FIX_CALLS_BUDGET = FIX_TOTAL_BYTES - 550_000  # the registry and the index take the rest


def write_fixtures(index: list[dict]) -> dict[str, Any]:
    """The committed sample. Every called function gets calls (its smallest kept one at least, when that
    is under FIX_MAX_BYTES); the number of calls and the per-file byte limit shrink together until the
    call files fit the budget."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    plans: dict[tuple[int, int], dict[str, str]] = {c: {} for c in FIX_COMBOS}
    smallest: dict[str, str] = {}
    skipped = []
    for ix in index:
        data = json.loads((OUT / f"{ix['stem']}.json").read_text(encoding="utf-8"))
        if not data["calls"]:
            continue
        info = {k: v for k, v in data.items() if k != "calls"}
        by_size = sorted(data["calls"], key=lambda c: len(dumps(c)))
        raising = [c for c in by_size if "raises" in c["why"]]
        fallback = (raising or by_size)[0]
        if len(dumps([fallback])) <= FIX_MAX_BYTES:
            smallest[ix["stem"]] = render_file({**info, "kept": 1}, [fallback])
        else:
            skipped.append(ix["stem"])
        for combo in FIX_COMBOS:
            calls = pick_sample(data["calls"], combo[0], combo[1])
            if calls and len(dumps(calls)) <= combo[1]:
                plans[combo][ix["stem"]] = render_file({**info, "kept": len(calls)}, calls)
    chosen = FIX_COMBOS[-1]
    for combo in FIX_COMBOS:
        if sum(len(t) for t in {**smallest, **plans[combo]}.values()) <= FIX_CALLS_BUDGET:
            chosen = combo
            break
    texts = {**smallest, **plans[chosen]}
    for stem, text in texts.items():
        (FIXTURES / f"{stem}.json").write_text(text, encoding="utf-8")
    reg = json.loads((OUT / "_registry.json").read_text(encoding="utf-8"))
    (FIXTURES / "_registry.json").write_text(json.dumps(reg, separators=(",", ":")) + "\n", encoding="utf-8")
    slim = json.loads((OUT / "_index.json").read_text(encoding="utf-8"))
    (FIXTURES / "_index.json").write_text(json.dumps(slim, separators=(",", ":")) + "\n", encoding="utf-8")
    keep = {f"{stem}.json" for stem in texts} | {"_registry.json", "_index.json"}
    pruned = _prune(FIXTURES, keep)
    total = sum(f.stat().st_size for f in FIXTURES.glob("*.json"))
    biggest = max(f.stat().st_size for f in FIXTURES.glob("*.json") if f.name not in META_FILES)
    return {
        "files": len(texts), "bytes": total, "combo_max_calls_max_bytes": chosen, "biggest_file": biggest,
        "no_fixture_all_calls_over_limit": skipped, "pruned_stale": pruned,
    }  # fmt: skip


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def parse_corpus(argv: list[str]) -> list[str]:
    if "--corpus" in argv:
        return argv[argv.index("--corpus") + 1].split(",")
    return ["wide", "full"] if (HERE / "corpus" / "full.json").exists() else ["wide"]


def parse_limit(argv: list[str]) -> int:
    return int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 0


def cmd_record(argv: list[str]) -> int:
    global OUT, FIXTURES
    if "--out" in argv:  # a scratch run (the determinism test): outputs and fixtures go under this directory
        OUT = Path(argv[argv.index("--out") + 1]) / "calls"
        FIXTURES = Path(argv[argv.index("--out") + 1]) / "fixtures"
    corpora = parse_corpus(argv)
    limit = parse_limit(argv)
    t0 = time.time()
    install_hook()
    import anime_character_creator.character as ch
    import anime_character_creator.urlstate as us

    # every def of the five modules must have been wrapped
    for m in TARGETS:
        mod = sys.modules[m]
        tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
        names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        got = {r.name for r in RECS if r.module == m and r.kind == "function"}
        if names != got:
            raise RuntimeError(f"{m}: defs {sorted(names - got)} not wrapped, or wrapped but not defs {sorted(got - names)}")
    reg = build_registry()
    print(f"registry: {len(reg)} constants ({len(REFS)} ids)", flush=True)
    t_imp = time.time() - t0
    hashes: list = []
    errs: collections.Counter = collections.Counter()
    t1 = time.time()
    n = 0
    it = iter_cases(corpora, limit)
    while True:
        PHASE[0] = 1  # the corpus code that builds the next case calls package functions too (Expression.applied_to, ...)
        RUN[0] = True
        try:
            cid, kind, payload = next(it)
        except StopIteration:
            break
        finally:
            RUN[0] = False
            PHASE[0] = 2
        run_one(ch, us, cid, kind, payload, hashes, True, errs)
        n += 1
        if n % 1000 == 0:
            print(f"  {n} cases, {time.time() - t1:.0f}s", flush=True)
    t_run = time.time() - t1
    bad = registry_value_check(reg)
    if bad:
        print("WARNING: constants changed during the run:", bad)
    meta = {
        "corpora": corpora,
        "limit": limit,
        "cases": n,
        "renders": len(hashes),
        "errors": dict(errs),
        "python": sys.version.split()[0],
        "seconds_import": round(t_imp, 1),
        "seconds_render": round(t_run, 1),
        "seed": SEED,
        "caps": {"first": FIRST_N, "sample": SAMPLE_N, "raises": RAISE_CAP, "bytes": MAX_BYTES},
        "registry_mutated": bad,
        "registry_unregistered": dict(UNREGISTERED),
    }
    res = write_outputs(meta, reg)
    (OUT / "_wrapped_hashes.json").write_text(json.dumps({"corpora": corpora, "limit": limit, "hashes": hashes}) + "\n", encoding="utf-8")
    fx = write_fixtures(res["index"])
    ix = res["index"]
    print(f"recorded {len(ix)} functions from {n} cases ({len(hashes)} renders) in {t_run:.0f}s render + {t_imp:.1f}s import")
    print(f"called {sum(1 for i in ix if i['total_calls'])}, never called {sum(1 for i in ix if not i['total_calls'])}")
    print(f"distinct calls {sum(i['distinct'] for i in ix)}, kept {sum(i['kept'] for i in ix)}, errors {dict(errs)}")
    print("fixtures:", fx)
    return 0


def plain_hashes(corpora: list[str], limit: int) -> list:
    """Render the corpus with NO hook and NO wrapper (this process never installs one)."""
    _bootstrap.assert_package_location()
    import anime_character_creator.character as ch
    import anime_character_creator.urlstate as us

    if hasattr(ch.render_character, "__wrapped__"):
        raise RuntimeError("plain pass found a wrapped render_character")
    RUN_ON[0] = False
    hashes: list = []
    errs: collections.Counter = collections.Counter()
    for cid, kind, payload in iter_cases(corpora, limit):
        run_one(ch, us, cid, kind, payload, hashes, False, errs)
    return hashes


def cmd_check(argv: list[str]) -> int:
    path = OUT / "_wrapped_hashes.json"
    if not path.exists():
        print("run `calls.py record` first")
        return 2
    saved = json.loads(path.read_text(encoding="utf-8"))
    corpora = saved["corpora"]
    limit = parse_limit(argv) or saved["limit"]
    t0 = time.time()
    plain = plain_hashes(corpora, limit)
    got = saved["hashes"][: len(plain)]
    same = plain == got
    diff = [i for i, (a, b) in enumerate(zip(plain, got)) if a != b]
    print(f"wrapped renders {len(got)}, plain renders {len(plain)}, identical={same}, first diffs {diff[:5]}, {time.time() - t0:.0f}s")
    print("exceptions: wrapped", sum(h[1].startswith("EXC") for h in got), "plain", sum(h[1].startswith("EXC") for h in plain))
    rc = 0 if same and len(plain) >= 300 else 1
    p = subprocess.run([sys.executable, str(Path(__file__).resolve()), "selftest"], env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return rc or p.returncode


PROBE = """\
from dataclasses import dataclass
def inner(x, y=2.0):
    return x * y
def outer(a, b):
    return inner(a) + inner(b, y=3.0)
def boom(x):
    if x < 0:
        raise ValueError('neg')
    return x
def mutate(xs):
    xs.append(1)
    return len(xs)
def takes_fn(f, x):
    return f(x)
def makes_fn(k):
    return lambda v: v + k
def gen(n):
    return (i for i in range(n))
@dataclass(frozen=True)
class P:
    x: float
    @property
    def twice(self):
        return inner(self.x, 2.0)
    def shifted(self, d):
        return P(self.x + d)
def use_p(p):
    return p.twice + p.shifted(1.0).twice
def neg0(z):
    return z
"""


def cmd_selftest(argv: list[str]) -> int:
    """The wrapper on a synthetic module: interception of internal calls, pass-through, exceptions, mutation."""
    import importlib
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="calls_selftest_"))
    (tmp / "probe_mod.py").write_text(PROBE, encoding="utf-8")
    sys.path.insert(0, str(tmp))
    builtins.__cw = func_wrapper  # type: ignore[attr-defined]
    builtins.__cwc = class_wrapper  # type: ignore[attr-defined]
    sys.meta_path.insert(0, RecordingFinder(("probe_mod",)))
    sys.dont_write_bytecode = True
    RUN[0] = True
    PHASE[0] = 2
    pm = importlib.import_module("probe_mod")
    ok = True

    def check(cond: bool, what: str) -> None:
        nonlocal ok
        print(("ok   " if cond else "FAIL ") + what)
        ok = ok and cond

    by = {r.name: r for r in RECS}
    want = {"inner", "outer", "boom", "mutate", "takes_fn", "makes_fn", "gen", "use_p", "neg0", "P.twice", "P.shifted"}
    check(set(by) == want, "every def, method and property wrapped: " + ",".join(sorted(by)))
    check(pm.outer(1.5, 2.5) == 1.5 * 2.0 + 2.5 * 3.0, "outer returns the same value")
    check(by["inner"].total == 2, "internal calls from outer are intercepted (inner total=%d)" % by["inner"].total)
    check(by["outer"].total == 1 and by["outer"].distinct == 1, "outer counted once")
    pm.outer(1.5, 2.5)
    check(by["inner"].total == 4 and by["inner"].distinct == 2, "repeat calls count but dedupe (total=%d distinct=%d)" % (by["inner"].total, by["inner"].distinct))
    e = final_entries(by["inner"])
    check(len(e) == 2 and e[0]["count"] == 2, "kept entries carry the count")
    check(e[1]["kwargs"] == {"y": "f:" + _pack(3.0).hex()}, "kwargs kept by name: %r" % (e[1]["kwargs"],))
    try:
        pm.boom(-1.0)
        check(False, "boom must raise")
    except ValueError as ex:
        check(str(ex) == "neg", "exception passes through unchanged")
    pm.boom(2.0)
    eb = final_entries(by["boom"])
    check(any(x["result"] == {"exc": "ValueError", "msg": "neg"} and "raises" in x["why"] for x in eb), "raising call kept with {exc, msg}")
    lst = [0]
    check(pm.mutate(lst) == 2 and lst == [0, 1], "mutating function still mutates the caller's list")
    check(by["mutate"].mutated == 1, "argument mutation detected")
    check(pm.takes_fn(lambda v: v + 1, 1) == 2 and by["takes_fn"].unrec == 1, "callable argument is unrecordable but the call works")
    f = pm.makes_fn(3)
    check(f(1) == 4 and by["makes_fn"].unrec == 1, "callable result is unrecordable but returned")
    g = pm.gen(3)
    check(list(g) == [0, 1, 2] and by["gen"].lazy == 1, "generator result flagged and not consumed")
    p = pm.P(1.0)
    check(pm.use_p(p) == 2.0 + 4.0, "frozen dataclass property and method pass through")
    check(by["P.twice"].total == 2 and by["P.shifted"].total == 1, "property and method wrapped (twice=%d shifted=%d)" % (by["P.twice"].total, by["P.shifted"].total))
    ep = final_entries(by["P.shifted"])
    check(ep[0]["args"][0] == {"dc": "P", "f": {"x": "f:" + _pack(1.0).hex()}}, "dataclass argument encoded: %s" % dumps(ep[0]["args"]))
    pm.neg0(-0.0)
    pm.neg0(0.0)
    pm.neg0(1)
    pm.neg0(True)
    check(by["neg0"].distinct == 4, "-0.0, 0.0, 1 and True are four distinct calls (got %d)" % by["neg0"].distinct)
    check(any("special:negzero" in x["why"] for x in final_entries(by["neg0"])), "-0.0 kept as special")
    check(len({sha_of(x["args"], x["kwargs"]) for x in final_entries(by["neg0"])}) == 4, "sha256 distinct as well")
    RUN[0] = False
    n = by["inner"].total
    pm.inner(9.0)
    check(by["inner"].total == n, "recording off: nothing counted")
    print("selftest", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# --------------------------------------------------------------------------
# replay (Python decoder: proves the recordings are faithful and the functions pure)
# --------------------------------------------------------------------------
def py_decode(v: Any, classes: dict[str, type]) -> Any:
    """The inverse of `enc`, the way the TypeScript side has to read it."""
    if v is None:
        return None
    if isinstance(v, str):
        tag, body = v[:2], v[2:]
        if tag == "f:":
            return struct.unpack(">d", bytes.fromhex(body))[0]
        if tag == "i:":
            return int(body)
        if tag == "b:":
            return body == "1"
        if tag == "s:":
            return body
        raise ValueError("bad scalar " + v)
    if "t" in v:
        return tuple(py_decode(x, classes) for x in v["t"])
    if "l" in v:
        return [py_decode(x, classes) for x in v["l"]]
    if "d" in v:
        return {py_decode(a, classes): py_decode(b, classes) for a, b in v["d"]}
    if "set" in v:
        items = [py_decode(x, classes) for x in v["set"]]
        return frozenset(items) if v.get("frozen") else set(items)
    if "dc" in v:
        return classes[v["dc"]](**{k: py_decode(x, classes) for k, x in v["f"].items()})
    if "ref" in v:
        return REG_OBJS[v["ref"]]
    raise ValueError("bad value " + dumps(v)[:80])


def cmd_replay(argv: list[str]) -> int:
    """In a plain process (no hook), decode every recorded call, call the real function, compare."""
    where = argv[argv.index("--dir") + 1] if "--dir" in argv else "out"
    root = OUT if where == "out" else FIXTURES
    _bootstrap.assert_package_location()
    mods = [importlib.import_module(m) for m in TARGETS]
    classes = {n: v for m in mods for n, v in vars(m).items() if isinstance(v, type) and DCINFO.get(v, None) is not False and hasattr(v, "__dataclass_fields__")}
    reg = build_registry()
    recorded = json.loads((OUT / "_registry.json").read_text(encoding="utf-8"))["constants"]
    changed = [n for n in recorded if n not in reg or dumps(reg[n]["value"]) != dumps(recorded[n]["value"])]
    extra = [n for n in reg if n not in recorded]
    print(f"registry: {len(reg)} now, {len(recorded)} recorded, differing {changed[:5]}, new {extra[:5]}")
    bad = 0
    total = 0
    t0 = time.time()
    mism: list[str] = []
    for f in sorted(root.glob("*.json")):
        if f.name in META_FILES:
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        name, module = data["function"], data["module"]
        mod = sys.modules["anime_character_creator." + module]
        for c in data["calls"]:
            total += 1
            try:
                args = [py_decode(a, classes) for a in c["args"]]
                kwargs = {k: py_decode(x, classes) for k, x in c["kwargs"].items()}
            except Exception as e:  # a decode failure is a bug in the recording
                bad += 1
                mism.append(f"{name}: decode failed {type(e).__name__}: {e}")
                continue
            # the decoded arguments must encode back to the recorded text
            BUDGET[0] = 10**9
            if dumps([enc(a) for a in args]) != dumps(c["args"]) or dumps({k: enc(x) for k, x in sorted(kwargs.items())}) != dumps(c["kwargs"]):
                bad += 1
                mism.append(f"{name}: arguments do not round-trip")
                continue
            try:
                if "." in name:
                    cls, attr = name.split(".", 1)
                    if data["kind"] == "property":
                        res = getattr(args[0], attr)
                    else:
                        res = getattr(getattr(mod, cls), attr)(*args, **kwargs)
                else:
                    res = getattr(mod, name)(*args, **kwargs)
                got: Any = enc(res)
            except Exception as e:
                got = {"exc": type(e).__name__, "msg": str(e)}
            if dumps(got) != dumps(c["result"]):
                bad += 1
                mism.append(f"{name}: result differs: recorded {dumps(c['result'])[:100]} now {dumps(got)[:100]}")
    for m in mism[:20]:
        print("MISMATCH", m)
    print(f"replayed {total} calls from {root}, {bad} mismatches, {time.time() - t0:.0f}s")
    return 1 if bad else 0


def load_index() -> dict[str, Any]:
    p = OUT / "_index.json"
    if not p.exists():
        raise SystemExit("run `calls.py record` first")
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_list_uncalled(argv: list[str]) -> int:
    idx = load_index()
    un = [f for f in idx["functions"] if not f["total_calls"]]
    for f in un:
        print(f"{f['module']}.{f['function']}  line {f['line']}  {f['signature']}")
    print(f"{len(un)} of {len(idx['functions'])} functions were never called by the corpus")
    return 0


def cmd_sample(argv: list[str]) -> int:
    idx = load_index()
    print(write_fixtures(idx["functions"]))
    return 0


# --------------------------------------------------------------------------
# doc tables
# --------------------------------------------------------------------------
def md_tables(idx: dict[str, Any]) -> dict[str, str]:
    fns = idx["functions"]
    fx = {p.stem for p in FIXTURES.glob("*.json") if p.name not in META_FILES}

    def row(f: dict) -> str:
        return (
            f"| `{f['stem']}` | {f['module']} | {f['line']} | {f['total_calls']} | {f['calls_by_phase']['import']} / {f['calls_by_phase']['build']} | {f['distinct']} | {f['kept']} "
            f"| {f['unrecordable']} | {f['skipped_large']} | {f['raised_distinct']} | {'yes' if f['stem'] in fx else 'no'} |"
        )

    head = (
        "| function | module | line | total calls | import / corpus build | distinct | kept | unrecordable | skipped large | raising (distinct) | in fixtures |\n"
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|\n"
    )
    called = [f for f in fns if f["total_calls"]]
    out = {"functions": head + "\n".join(row(f) for f in called) + "\n"}
    by_mod: collections.Counter = collections.Counter()
    for f in fns:
        by_mod[(f["module"], f["kind"])] += 1
    out_bytes = sum(p.stat().st_size for p in OUT.glob("*.json"))
    fx_bytes = sum(p.stat().st_size for p in FIXTURES.glob("*.json"))
    fx_kept = [json.loads(p.read_text(encoding="utf-8"))["kept"] for p in FIXTURES.glob("*.json") if p.name not in META_FILES]
    fx_calls, fx_max_calls = sum(fx_kept), max(fx_kept)
    fx_max_bytes = max(p.stat().st_size for p in FIXTURES.glob("*.json") if p.name not in META_FILES)
    meta = idx["meta"]
    uncalled = [f for f in fns if not f["total_calls"]]
    unrec_fns = [f for f in fns if f["unrecordable"]]
    nokept = [f for f in fns if f["total_calls"] and not f["kept"]]
    out["summary"] = (
        "| | |\n|---|---|\n"
        + f"| corpora | {', '.join(meta['corpora'])} ({meta['cases']} cases, {meta['renders']} renders, {sum(meta['errors'].values())} driver calls that raised: render, urlstate) |\n"
        + f"| functions recorded | {len(fns)} ("
        + ", ".join(f"{m} {k}: {n}" for (m, k), n in sorted(by_mod.items()))
        + ") |\n"
        + f"| called at least once | {len(fns) - len(uncalled)} |\n"
        + f"| never called | {len(uncalled)} |\n"
        + f"| with some unrecordable calls | {len(unrec_fns)} |\n"
        + f"| called but no call kept | {len(nokept)} |\n"
        + f"| total calls | {sum(f['total_calls'] for f in fns)} |\n"
        + f"| distinct calls | {sum(f['distinct'] for f in fns)} |\n"
        + f"| calls kept in `out/calls` | {sum(f['kept'] for f in fns)} ({out_bytes} bytes in {len(list(OUT.glob('*.json')))} files) |\n"
        + f"| calls in `fixtures/calls` | {fx_calls} ({fx_bytes} bytes in {len(list(FIXTURES.glob('*.json')))} files, limit 3,000,000; at most {fx_max_calls} calls and {fx_max_bytes} bytes per function file) |\n"
        + f"| time | record {meta['seconds_render']} s of rendering and {meta['seconds_import']} s of import, single process |\n"
    )
    un = [f for f in fns if not f["total_calls"]]
    out["uncalled"] = "".join(f"- `{f['module']}.{f['function']}` (line {f['line']}), `{f['signature']}`\n" for f in un) or "- none\n"
    unrec = [f for f in fns if f["unrecordable"]]
    out["unrecordable"] = (
        "| function | unrecordable calls | total calls | reasons |\n|---|---:|---:|---|\n"
        + "\n".join(f"| `{f['stem']}` | {f['unrecordable']} | {f['total_calls']} | {'; '.join(f'{k} x{v}' for k, v in sorted(f['unrecordable_reasons'].items()))} |" for f in unrec)
        + "\n"
    )
    nokept = [f for f in fns if f["total_calls"] and not f["kept"]]
    out["nokept"] = "".join(
        f"- `{f['stem']}`: {f['total_calls']} calls, {f['unrecordable']} unrecordable, {f['skipped_large']} skipped as large\n" for f in nokept
    ) or "- none\n"
    mut = [f for f in fns if f["mutates_arguments"]]
    out["mutating"] = "".join(f"- `{f['stem']}` ({f['mutates_arguments']} distinct calls changed an argument)\n" for f in mut) or "- none\n"
    reg = json.loads((OUT / "_registry.json").read_text(encoding="utf-8"))["constants"]
    lines = ["| ref name | module | kind | level |\n|---|---|---|---:|"]
    for name, info in sorted(reg.items()):
        lines.append(f"| `{name}` | {info['module']} | {info['kind']} | {info['level']} |")
    out["registry"] = "\n".join(lines) + "\n"
    return out


def cmd_doc(argv: list[str]) -> int:
    idx = load_index()
    text = DOCS.read_text(encoding="utf-8")
    for key, body in md_tables(idx).items():
        pat = re.compile(rf"(<!-- BEGIN:{key} -->\n).*?(<!-- END:{key} -->)", re.S)
        if not pat.search(text):
            print(f"marker {key} missing in {DOCS}")
            return 1
        text = pat.sub(lambda m: m.group(1) + body + m.group(2), text)
    DOCS.write_text(text, encoding="utf-8")
    print("refreshed tables in", DOCS)
    return 0


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else ""
    fn = {
        "record": cmd_record,
        "replay": cmd_replay,
        "check": cmd_check,
        "selftest": cmd_selftest,
        "list-uncalled": cmd_list_uncalled,
        "sample": cmd_sample,
        "doc": cmd_doc,
    }.get(mode)
    if fn is None:
        print(__doc__)
        return 2
    return fn(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
