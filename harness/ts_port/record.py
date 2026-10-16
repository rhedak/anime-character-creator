"""Record REAL numeric calls made while rendering the wide corpus.

An AST-instrumenting import hook rewrites four modules of the frozen Python
package (character, skeleton, colorutil, presets) so that every numeric
formatting, `%`, `**`, round/sum/sorted/min/max and selected math call also
reports its arguments and result to a recorder. The rewrite is meant to be
behaviour-neutral; `check` proves it by comparing every rendered SVG against a
plain, non-instrumented process.

Modes (run with the worktree's src on PYTHONPATH, never with -I):

  record.py record [--workers N] [--limit-cases N]
      render the corpus instrumented; writes out/real-calls.json (full),
      out/inst_hashes.json, out/record-summary.json, and then the committed
      fixtures/real-calls.sample.json
  record.py plain  [--limit-cases N]
      render the same corpus with NO hook; writes out/plain_hashes.json
  record.py check
      compare out/inst_hashes.json with out/plain_hashes.json
  record.py sample
      rebuild fixtures/real-calls.sample.json from out/real-calls.json

Value encoding in all JSON: float "f:" + 16 hex digits of the big-endian
IEEE-754 double; int "i:" + decimal; bool "b:1"/"b:0"; str "s:" + text;
lists/tuples as JSON lists of encoded values; None as null.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.abc
import importlib.machinery
import json
import math
import struct
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE_SRC = HERE.parent.parent / "src"
OUT = HERE / "out"
FIXTURES = HERE / "fixtures"
TARGETS = {
    "anime_character_creator.character",
    "anime_character_creator.skeleton",
    "anime_character_creator.colorutil",
    "anime_character_creator.presets",
}
MATH_FUNCS = ("sin", "cos", "atan2", "acos", "hypot", "sqrt", "radians", "degrees", "copysign")
BUILTIN_WRAPPED = ("round", "sum", "sorted", "min", "max")

_pack = struct.Struct(">d").pack


# --------------------------------------------------------------------------
# value keys and encoding
# --------------------------------------------------------------------------
def K(v):
    """A hashable key that tells values apart exactly (bits for floats, type for the rest)."""
    t = type(v)
    if t is float:
        return _pack(v)
    if t is int:
        return v
    if t is bool:
        return ("b", v)
    if t is str:
        return ("s", v)
    if t is tuple or t is list:
        return (t.__name__, tuple([K(x) for x in v]))
    if v is None:
        return ("n",)
    return ("o", t.__name__, repr(v))


def E(v):
    """JSON encoding of one recorded value."""
    t = type(v)
    if t is float:
        return "f:" + _pack(v).hex()
    if t is bool:
        return "b:1" if v else "b:0"
    if t is int:
        return "i:" + str(v)
    if t is str:
        return "s:" + v
    if t is tuple or t is list:
        return [E(x) for x in v]
    if v is None:
        return None
    return "o:" + type(v).__name__ + ":" + repr(v)


def _fresh_state():
    return {
        "fmt": {},
        "bare": {},
        "bare_types": {},
        "round": {},
        "sum": {},
        "mod": {},
        "pow": {},
        "math": {n: {} for n in MATH_FUNCS},
        "minmax": {},
        "hits": {},
    }


class Recorder:
    """Receives calls from the instrumented modules. Every method returns the
    exact value the original expression produced."""

    def __init__(self):
        self.s = _fresh_state()
        self.minmax_plain_cap = 100_000
        self.minmax_inf_cap = 100_000
        self.minmax_overflow = Counter()
        self._nplain = 0
        self._ninf = 0

    def reset(self):
        self.s = _fresh_state()
        self._nplain = 0
        self._ninf = 0
        self.minmax_overflow.clear()

    # f-string with a constant f/x spec and no conversion
    def fmt(self, v, spec, loc):
        s = self.s
        h = s["hits"]
        h[("fmt", loc)] = h.get(("fmt", loc), 0) + 1
        k = (spec, _pack(v)) if type(v) is float else (spec, K(v))
        d = s["fmt"]
        e = d.get(k)
        if e is None:
            d[k] = [1, loc, v, format(v, spec)]
        else:
            e[0] += 1
        return v

    # bare f-string value (no spec, no conversion)
    def bare(self, v, loc):
        s = self.s
        h = s["hits"]
        h[("bare", loc)] = h.get(("bare", loc), 0) + 1
        t = type(v)
        bt = s["bare_types"].setdefault(loc, {})
        bt[t.__name__] = bt.get(t.__name__, 0) + 1
        if t is str:
            return v
        k = K(v)
        d = s["bare"]
        e = d.get(k)
        if e is None:
            d[k] = [1, loc, v, format(v, "")]
        else:
            e[0] += 1
        return v

    def mod(self, a, b, loc):
        r = a % b
        if type(a) is not str:
            s = self.s
            h = s["hits"]
            h[("mod", loc)] = h.get(("mod", loc), 0) + 1
            k = (K(a), K(b))
            d = s["mod"]
            e = d.get(k)
            if e is None:
                d[k] = [1, loc, a, b, r]
            else:
                e[0] += 1
        return r

    def pow(self, a, b, loc):
        r = a**b
        s = self.s
        h = s["hits"]
        h[("pow", loc)] = h.get(("pow", loc), 0) + 1
        k = (K(a), K(b))
        d = s["pow"]
        e = d.get(k)
        if e is None:
            d[k] = [1, loc, a, b, r]
        else:
            e[0] += 1
        return r

    def w_round(self, loc, x, *a, **kw):
        r = round(x, *a, **kw)
        nd = a[0] if a else kw.get("ndigits")
        s = self.s
        h = s["hits"]
        h[("round", loc)] = h.get(("round", loc), 0) + 1
        k = (K(x), K(nd))
        d = s["round"]
        e = d.get(k)
        if e is None:
            d[k] = [1, loc, x, nd, r]
        else:
            e[0] += 1
        return r

    def w_sum(self, loc, it, *a, **kw):
        items = list(it)
        r = sum(items, *a, **kw)
        start = a[0] if a else kw.get("start", 0)
        s = self.s
        h = s["hits"]
        h[("sum", loc)] = h.get(("sum", loc), 0) + 1
        k = (tuple([K(x) for x in items]), K(start))
        d = s["sum"]
        e = d.get(k)
        if e is None:
            d[k] = [1, loc, items, start, r]
        else:
            e[0] += 1
        return r

    def _minmax(self, name, fn, loc, args, kw):
        key = kw.get("key")
        if len(args) == 1:
            items = list(args[0])
            r = fn(items, **kw)
        else:
            items = args
            r = fn(*args, **kw)
        s = self.s
        h = s["hits"]
        h[("minmax", loc)] = h.get(("minmax", loc), 0) + 1
        n = len(items)
        if n < 2:
            return r
        keys = [key(x) for x in items] if key is not None else items
        try:
            tie = len(set(keys)) < n
        except TypeError:
            tie = any(keys[i] == keys[j] for i in range(n) for j in range(i + 1, min(n, 60)))
        if not tie:
            return r
        kk = (name, tuple([K(x) for x in items]), key is not None, loc)
        d = s["minmax"]
        e = d.get(kk)
        if e is not None:
            e[0] += 1
            return r
        # informative: two tied items that are not bit-identical (0.0 vs -0.0, 1 vs 1.0, or key ties)
        inf = False
        m = min(n, 60)
        for i in range(m):
            for j in range(i + 1, m):
                if keys[i] == keys[j] and K(items[i]) != K(items[j]):
                    inf = True
                    break
            if inf:
                break
        if inf:
            if self._ninf >= self.minmax_inf_cap:
                self.minmax_overflow["informative"] += 1
                return r
            self._ninf += 1
        else:
            if self._nplain >= self.minmax_plain_cap:
                self.minmax_overflow["plain"] += 1
                return r
            self._nplain += 1
        d[kk] = [1, loc, name, items, key is not None, r, inf]
        return r

    def w_min(self, loc, *args, **kw):
        return self._minmax("min", min, loc, args, kw)

    def w_max(self, loc, *args, **kw):
        return self._minmax("max", max, loc, args, kw)

    def w_sorted(self, loc, it, **kw):
        items = list(it)
        r = sorted(items, **kw)
        key = kw.get("key")
        s = self.s
        h = s["hits"]
        h[("minmax", loc)] = h.get(("minmax", loc), 0) + 1
        n = len(items)
        if n < 2:
            return r
        keys = [key(x) for x in items] if key is not None else items
        try:
            tie = len(set(keys)) < n
        except TypeError:
            tie = any(keys[i] == keys[j] for i in range(min(n, 60)) for j in range(i + 1, min(n, 60)))
        if not tie:
            return r
        kk = ("sorted", tuple([K(x) for x in items]), key is not None, loc)
        d = s["minmax"]
        e = d.get(kk)
        if e is not None:
            e[0] += 1
            return r
        inf = any(keys[i] == keys[j] and K(items[i]) != K(items[j]) for i in range(min(n, 60)) for j in range(i + 1, min(n, 60)))
        if inf:
            if self._ninf >= self.minmax_inf_cap:
                self.minmax_overflow["informative"] += 1
                return r
            self._ninf += 1
        else:
            if self._nplain >= self.minmax_plain_cap:
                self.minmax_overflow["plain"] += 1
                return r
            self._nplain += 1
        d[kk] = [1, loc, "sorted", items, key is not None, r, inf]
        return r

    def make_math(self, name):
        f = getattr(math, name)
        dd_name = name

        def w(loc, *args):
            r = f(*args)
            s = self.s
            h = s["hits"]
            hk = ("math." + dd_name, loc)
            h[hk] = h.get(hk, 0) + 1
            k = tuple([K(x) for x in args])
            d = s["math"][dd_name]
            e = d.get(k)
            if e is None:
                d[k] = [1, loc, args, r]
            else:
                e[0] += 1
            return r

        return w


R = Recorder()
for _n in MATH_FUNCS:
    setattr(R, "m_" + _n, R.make_math(_n))


# --------------------------------------------------------------------------
# AST transform
# --------------------------------------------------------------------------
class Transform(ast.NodeTransformer):
    def __init__(self, fname):
        self.fname = fname
        self.sites = Counter()  # class -> static transformed sites
        self.site_locs: dict[str, set] = {}
        self.shadowed: set[str] = set()
        self.untransformed: list[str] = []

    def loc(self, node):
        return f"{self.fname}:{node.lineno}"

    def note(self, cls, node):
        self.sites[cls] += 1
        self.site_locs.setdefault(cls, set()).add(self.loc(node))

    def R(self, attr, node):
        return ast.copy_location(ast.Attribute(ast.Name("_R", ast.Load()), attr, ast.Load()), node)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)) and node.id in BUILTIN_WRAPPED + ("math",):
            self.shadowed.add(node.id)
        return node

    def visit_arg(self, node):
        if node.arg in BUILTIN_WRAPPED + ("math",):
            self.shadowed.add(node.arg)
        return node

    def visit_FormattedValue(self, node):
        node = self.generic_visit(node)
        if node.conversion != -1:
            return node
        spec = None
        if node.format_spec is not None:
            vals = node.format_spec.values
            if len(vals) == 1 and isinstance(vals[0], ast.Constant) and isinstance(vals[0].value, str):
                spec = vals[0].value
            else:
                self.untransformed.append(f"{self.loc(node)} dynamic spec")
                return node
        if spec is None:
            node.value = ast.copy_location(
                ast.Call(self.R("bare", node), [node.value, ast.Constant(self.loc(node))], []), node.value
            )
            self.note("bare", node)
        elif spec.endswith("f") or spec.endswith("x"):
            node.value = ast.copy_location(
                ast.Call(self.R("fmt", node), [node.value, ast.Constant(spec), ast.Constant(self.loc(node))], []),
                node.value,
            )
            self.note("fmt", node)
        else:
            self.untransformed.append(f"{self.loc(node)} other spec {spec!r}")
        return node

    def visit_BinOp(self, node):
        node = self.generic_visit(node)
        if isinstance(node.op, (ast.Mod, ast.Pow)):
            name = "mod" if isinstance(node.op, ast.Mod) else "pow"
            self.note(name, node)
            return ast.copy_location(
                ast.Call(self.R(name, node), [node.left, node.right, ast.Constant(self.loc(node))], []), node
            )
        return node

    def visit_AugAssign(self, node):
        node = self.generic_visit(node)
        if isinstance(node.op, (ast.Mod, ast.Pow)):
            self.untransformed.append(f"{self.loc(node)} augassign {type(node.op).__name__}")
        return node

    def visit_Call(self, node):
        node = self.generic_visit(node)
        f = node.func
        if isinstance(f, ast.Name) and f.id in BUILTIN_WRAPPED:
            self.note(f.id, node)
            node.func = self.R("w_" + f.id, f)
            node.args = [ast.Constant(self.loc(node))] + node.args
        elif (
            isinstance(f, ast.Attribute)
            and isinstance(f.value, ast.Name)
            and f.value.id == "math"
            and f.attr in MATH_FUNCS
        ):
            self.note("math." + f.attr, node)
            node.func = self.R("m_" + f.attr, f)
            node.args = [ast.Constant(self.loc(node))] + node.args
        elif isinstance(f, ast.Attribute) and f.attr == "sort":
            pass
        return node


class Loader(importlib.machinery.SourceFileLoader):
    """Compiles the transformed AST every time; never reads or writes a .pyc."""

    transforms: dict[str, Transform] = {}

    def get_code(self, fullname):
        data = self.get_data(self.path)
        tree = ast.parse(data, self.path)
        fname = Path(self.path).name
        t = Transform(fname)
        tree = t.visit(tree)
        ast.fix_missing_locations(tree)
        Loader.transforms[fname] = t
        return compile(tree, self.path, "exec", dont_inherit=True)

    def exec_module(self, module):
        module.__dict__["_R"] = R
        super().exec_module(module)


class Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname not in TARGETS:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if spec is None or not isinstance(spec.loader, importlib.machinery.SourceFileLoader):
            return spec
        spec.loader = Loader(fullname, spec.origin)
        spec.cached = None
        return spec


def install_hook():
    sys.dont_write_bytecode = True
    sys.meta_path.insert(0, Finder())


def import_package(instrumented: bool):
    import anime_character_creator as acc

    assert Path(acc.__file__).resolve().is_relative_to(WORKTREE_SRC), acc.__file__
    return acc


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def render_chunk(args):
    """Render cases[lo:hi] with id_prefix '' and 'x'; return hashes, error counts and the recorder state."""
    lo, hi = args
    from anime_character_creator.character import render_character

    R.reset()
    hashes = []
    errs = Counter()
    for i in range(lo, hi):
        p = CASES[i]
        for pref in ("", "x"):
            try:
                svg = render_character(p, id_prefix=pref)
                hashes.append(hashlib.sha256(svg.encode()).hexdigest())
            except Exception as e:  # data
                msg = f"{type(e).__name__}: {str(e)[:120]}"
                errs[msg] += 1
                hashes.append("EXC " + msg)
    return lo, hashes, errs, R.s, dict(R.minmax_overflow)


CASES: list = []


def merge(dst, src):
    for k in ("fmt", "bare", "round", "sum", "mod", "pow", "minmax"):
        d = dst[k]
        for kk, v in src[k].items():
            e = d.get(kk)
            if e is None:
                d[kk] = v
            else:
                e[0] += v[0]
    for fn in MATH_FUNCS:
        d = dst["math"][fn]
        for kk, v in src["math"][fn].items():
            e = d.get(kk)
            if e is None:
                d[kk] = v
            else:
                e[0] += v[0]
    for kk, v in src["hits"].items():
        dst["hits"][kk] = dst["hits"].get(kk, 0) + v
    for loc, tc in src["bare_types"].items():
        t = dst["bare_types"].setdefault(loc, {})
        for n, c in tc.items():
            t[n] = t.get(n, 0) + c


def load_cases(limit):
    sys.path.insert(0, str(HERE))
    import corpus_wide

    cases = list(corpus_wide.corpus())
    if limit:
        cases = cases[:limit]
    return cases, corpus_wide.STATS


def run_corpus(workers, limit, instrumented):
    global CASES
    CASES, stats = load_cases(limit)
    n = len(CASES)
    chunk = max(1, min(60, n // max(workers * 4, 1)))
    ranges = [(lo, min(lo + chunk, n)) for lo in range(0, n, chunk)]
    total = _fresh_state()
    hashes = [None] * (2 * n)
    errs = Counter()
    overflow = Counter()
    if workers > 1:
        import multiprocessing as mp

        pool = mp.get_context("fork").Pool(workers)
        it = pool.imap(render_chunk, ranges)
    else:
        pool = None
        it = map(render_chunk, ranges)
    t0 = time.time()
    for lo, hs, er, st, ov in it:
        hashes[2 * lo : 2 * lo + len(hs)] = hs
        errs.update(er)
        overflow.update(ov)
        if instrumented:
            merge(total, st)
    if pool:
        pool.close()
        pool.join()
    return n, hashes, errs, overflow, total, stats, time.time() - t0


# --------------------------------------------------------------------------
# serialisation
# --------------------------------------------------------------------------
def serialise(total, overflow):
    out = {
        "fmt": [[E(v[2]), k[0], v[3], v[0], v[1]] for k, v in total["fmt"].items()],
        "bare": [[E(v[2]), v[3], v[0], v[1]] for k, v in total["bare"].items()],
        "round": [[E(v[2]), E(v[3]), E(v[4]), v[0], v[1]] for v in total["round"].values()],
        "sum": [[E(v[2]), E(v[3]), E(v[4]), v[0], v[1]] for v in total["sum"].values()],
        "mod": [[E(v[2]), E(v[3]), E(v[4]), v[0], v[1]] for v in total["mod"].values()],
        "pow": [[E(v[2]), E(v[3]), E(v[4]), v[0], v[1]] for v in total["pow"].values()],
        "math": {
            fn: [[*[E(a) for a in v[2]], E(v[3]), v[0], v[1]] for v in total["math"][fn].values()] for fn in MATH_FUNCS
        },
    }
    mm = list(total["minmax"].values())
    inf = [v for v in mm if v[6]]
    plain = [v for v in mm if not v[6]]
    keep = (inf + plain)[:5000]
    out["minmax"] = [[v[2], E(v[3]), v[4], E(v[5]), v[0], v[1]] for v in keep]
    out["bare_types"] = {loc: tc for loc, tc in sorted(total["bare_types"].items())}
    out["meta"] = {
        "minmax_total_distinct_ties": len(mm),
        "minmax_informative_ties": len(inf),
        "minmax_kept": len(keep),
        "minmax_overflow": dict(overflow),
    }
    return out


# --------------------------------------------------------------------------
# sample reduction
# --------------------------------------------------------------------------
def dec_float(s):
    return struct.unpack(">d", bytes.fromhex(s[2:]))[0]


def vals_of(x):
    """All floats inside an encoded value (string or nested list)."""
    if isinstance(x, list):
        for y in x:
            yield from vals_of(y)
    elif isinstance(x, str) and x.startswith("f:"):
        yield dec_float(x)


def is_tie(x, nd):
    """x*10**nd has fractional part exactly one half (exact binary arithmetic)."""
    if math.isnan(x) or math.isinf(x):
        return False
    return (Fraction(x) * (10**nd)) % 1 == Fraction(1, 2)


def negzero(x):
    return x == 0.0 and math.copysign(1.0, x) < 0


def must_keep_flags(cls, e):
    """Reasons an entry must survive sampling."""
    flags = set()
    if cls == "fmt":
        v = dec_float(e[0]) if isinstance(e[0], str) and e[0].startswith("f:") else None
        spec = e[1]
        if v is not None:
            if spec.endswith("f") and spec.startswith(".") and spec[1:-1].isdigit() and is_tie(v, int(spec[1:-1])):
                flags.add("tie")
            if negzero(v):
                flags.add("negzero")
            if math.isnan(v) or math.isinf(v):
                flags.add("naninf")
            if e[2].startswith("-") and set(e[2]) <= set("-0."):
                flags.add("negzero_out")
    elif cls == "round":
        v = dec_float(e[0]) if isinstance(e[0], str) and e[0].startswith("f:") else None
        nd = int(e[1][2:]) if isinstance(e[1], str) and e[1].startswith("i:") else 0
        if v is not None:
            if is_tie(v, nd):
                flags.add("tie")
            if negzero(v):
                flags.add("negzero")
            if math.isnan(v) or math.isinf(v):
                flags.add("naninf")
        res = e[2]
        if isinstance(res, str) and res.startswith("f:") and negzero(dec_float(res)):
            flags.add("negzero")
    elif cls == "mod":
        fl = list(vals_of(e[0])) + list(vals_of(e[1]))
        ints = [int(x[2:]) for x in (e[0], e[1]) if isinstance(x, str) and x.startswith("i:")]
        if any(f < 0 or negzero(f) for f in fl) or any(i < 0 for i in ints):
            flags.add("negative_operand")
        if any(math.isnan(f) or math.isinf(f) for f in fl):
            flags.add("naninf")
    else:
        # generic: scan the encoded numeric fields before the count
        fl = []
        for x in e[:-2]:
            fl.extend(vals_of(x))
        if any(negzero(f) for f in fl):
            flags.add("negzero")
        if any(math.isnan(f) or math.isinf(f) for f in fl):
            flags.add("naninf")
    return flags


def reduce_class(cls, entries, cap, extra_keep=None):
    """Deterministic: sort by key, keep every flagged entry, then every k-th of the rest up to cap."""
    entries = sorted(entries, key=lambda e: json.dumps(e[:-2], sort_keys=True))
    keep, rest = [], []
    for e in entries:
        fl = must_keep_flags(cls, e)
        if extra_keep and extra_keep(e):
            fl.add("extra")
        (keep if fl else rest).append(e)
    stats = {"total": len(entries), "must_keep": len(keep)}
    room = cap - len(keep)
    if room < 0:
        keep = keep[:cap]
        room = 0
        stats["must_keep_truncated"] = True
    if room > 0 and rest:
        k = -(-len(rest) // room)
        picked = rest[::k]
    else:
        picked = []
    out = sorted(keep + picked, key=lambda e: json.dumps(e[:-2], sort_keys=True))
    stats["kept"] = len(out)
    return out, stats


def _size(x):
    return len(json.dumps(x, separators=(",", ":")))


def fit_bytes(entries, budget, maxn):
    """Deterministic, stratified: order by (item count, key), then the smallest stride that fits.

    Striding a list sorted by size keeps a mix of short and long entries rather
    than only the short ones."""
    entries = sorted(entries, key=lambda e: (len(json.dumps(e[0])), json.dumps(e[:-2])))
    if not entries:
        return []
    k = max(1, -(-len(entries) // maxn))
    while True:
        picked = entries[::k]
        if len(picked) <= maxn and _size(picked) <= budget:
            return sorted(picked, key=lambda e: json.dumps(e[:-2]))
        k += 1


def build_sample(full, cap=4000, sum_cap=800, minmax_cap=500, max_bytes=2_900_000, sum_budget=1_300_000, minmax_budget=450_000):
    """The committed sample: at most `cap` entries per class (per math function),
    always keeping the flagged entries (see must_keep_flags), at most `sum_cap`
    multi-item sums and `minmax_cap` ties, and under `max_bytes` in all."""
    sample, stats = {}, {}
    sums = full["sum"]
    multi = [e for e in sums if len(e[0]) > 2]
    small = [e for e in sums if len(e[0]) <= 2]
    sample_multi = fit_bytes(multi, sum_budget, sum_cap)
    sm, st = reduce_class("sum", small, cap - len(sample_multi))
    sample["sum"] = sorted(sample_multi + sm, key=lambda e: json.dumps(e[:-2]))
    stats["sum"] = {"total": len(sums), "multi_item_total": len(multi), "multi_item_kept": len(sample_multi), "short_total": len(small), "short_kept": len(sm)}
    # minmax: informative ties first (serialise ordered them so), then smallest entries, up to the cap
    mm = full["minmax"]
    sample["minmax"] = fit_bytes(mm, minmax_budget, minmax_cap)
    stats["minmax"] = {"total": len(mm), "kept": len(sample["minmax"])}
    scale = 1.0
    while True:
        c = int(cap * scale)
        for cls in ("fmt", "bare", "round", "mod", "pow"):
            sample[cls], stats[cls] = reduce_class(cls, full[cls], c)
        sample["math"] = {}
        for fn in MATH_FUNCS:
            sample["math"][fn], stats["math." + fn] = reduce_class("math", full["math"][fn], c)
        size = _size(sample)
        if size <= max_bytes or scale < 0.02:
            break
        scale *= 0.85
    stats["_cap_per_class_used"] = int(cap * scale)
    stats["_bytes"] = size
    return sample, stats


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def write_full(ser):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "real-calls.json"
    with open(p, "w") as fh:
        json.dump(ser, fh, separators=(",", ":"))
    return p


def ensure_gitignore():
    gi = HERE / ".gitignore"
    lines = gi.read_text().splitlines() if gi.exists() else []
    if "out/" not in [l.strip() for l in lines]:
        lines.append("out/")
        gi.write_text("\n".join(lines) + "\n")


def parse_args(argv):
    mode = argv[1] if len(argv) > 1 else "record"
    workers = 1
    limit = 0
    if "--workers" in argv:
        workers = int(argv[argv.index("--workers") + 1])
    if "--limit-cases" in argv:
        limit = int(argv[argv.index("--limit-cases") + 1])
    return mode, workers, limit


def main(argv):
    mode, workers, limit = parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    ensure_gitignore()
    if mode == "check":
        a = json.load(open(OUT / "inst_hashes.json"))
        b = json.load(open(OUT / "plain_hashes.json"))
        same = a["hashes"] == b["hashes"]
        diff = [i for i, (x, y) in enumerate(zip(a["hashes"], b["hashes"])) if x != y]
        print(f"instrumented renders {len(a['hashes'])}, plain renders {len(b['hashes'])}, identical={same}, first diffs {diff[:5]}")
        print("exceptions identical text too:", sum(h.startswith("EXC") for h in a["hashes"]), "inst vs", sum(h.startswith("EXC") for h in b["hashes"]), "plain")
        sys.exit(0 if same else 1)
    if mode == "sample":
        full = json.load(open(OUT / "real-calls.json"))
        write_sample(full)
        return
    if mode == "plain":
        pkg = import_package(False)
        import anime_character_creator.character as ch

        assert not hasattr(ch, "_R"), "plain mode must not be instrumented"
        n, hashes, errs, _ov, _t, stats, dt = run_corpus(workers, limit, False)
        json.dump({"hashes": hashes, "cases": n}, open(OUT / "plain_hashes.json", "w"))
        print(f"plain: {n} cases, {len(hashes)} renders, {dt:.1f}s, errors {dict(errs)}")
        return
    assert mode == "record", mode
    install_hook()
    import_package(True)
    import anime_character_creator.character as ch

    assert hasattr(ch, "_R"), "instrumentation did not apply"
    # Calls made while the package imports (module-level constants such as
    # _CROWN_TO_TEMPLE or the _fist() tables) happen once, in this process.
    import_state = R.s
    R.reset()
    n, hashes, errs, ov, total, stats, dt = run_corpus(workers, limit, True)
    merge(import_state, total)
    total = import_state
    json.dump({"hashes": hashes, "cases": n}, open(OUT / "inst_hashes.json", "w"))
    ser = serialise(total, ov)
    p = write_full(ser)
    # static transform report and coverage
    rep = {"static_sites": {}, "untransformed": {}, "shadowed": {}, "hit_lines": {}, "unhit_lines": {}}
    for fname, t in sorted(Loader.transforms.items()):
        rep["static_sites"][fname] = dict(t.sites)
        rep["untransformed"][fname] = t.untransformed
        rep["shadowed"][fname] = sorted(t.shadowed)
        for cls, locs in t.site_locs.items():
            key = "minmax" if cls in ("min", "max", "sorted") else cls
            hit = {loc for (c, loc) in total["hits"] if c == key and loc in locs}
            rep["hit_lines"].setdefault(cls, 0)
            rep["hit_lines"][cls] += len(hit)
            rep["unhit_lines"].setdefault(cls, []).extend(sorted(locs - hit))
    rep["renders"] = len(hashes)
    rep["cases"] = n
    rep["errors"] = dict(errs)
    rep["construct_errors"] = dict(stats["construct_errors"])
    rep["groups"] = dict(stats["groups"])
    rep["distinct"] = {
        "fmt": len(total["fmt"]),
        "bare": len(total["bare"]),
        "round": len(total["round"]),
        "sum": len(total["sum"]),
        "mod": len(total["mod"]),
        "pow": len(total["pow"]),
        "minmax_written": len(ser["minmax"]),
        **{"math." + fn: len(total["math"][fn]) for fn in MATH_FUNCS},
    }
    rep["calls"] = {
        "fmt": sum(v[0] for v in total["fmt"].values()),
        "bare_nonstr": sum(v[0] for v in total["bare"].values()),
        "round": sum(v[0] for v in total["round"].values()),
        "sum": sum(v[0] for v in total["sum"].values()),
        "mod": sum(v[0] for v in total["mod"].values()),
        "pow": sum(v[0] for v in total["pow"].values()),
        **{"math." + fn: sum(v[0] for v in total["math"][fn].values()) for fn in MATH_FUNCS},
    }
    rep["seconds"] = round(dt, 1)
    rep["meta"] = ser["meta"]
    json.dump(rep, open(OUT / "record-summary.json", "w"), indent=1)
    print(json.dumps(rep, indent=1)[:6000])
    print("full:", p, p.stat().st_size, "bytes")
    write_sample(ser)


def write_sample(full):
    FIXTURES.mkdir(parents=True, exist_ok=True)
    sample, stats = build_sample(full)
    p = FIXTURES / "real-calls.sample.json"
    with open(p, "w") as fh:
        json.dump(sample, fh, separators=(",", ":"))
    print("sample stats:", json.dumps(stats, indent=1))
    print("sample:", p, p.stat().st_size, "bytes")


if __name__ == "__main__":
    main(sys.argv)
