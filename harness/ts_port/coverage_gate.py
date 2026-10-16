"""Statement and branch coverage of the Python package by the full corpus, with `sys.monitoring`.

    coverage_gate.py run [--limit N] [--only PREFIX,...] [--min 98.0] [--out out/coverage-full.json]
    coverage_gate.py show FILE:FUNCTION      # source of the uncovered statements of one function

coverage.py is not installed in the venv, so this is a small counterpart (CPython 3.12 or newer:
`sys.monitoring` is new in 3.12). It runs every case of `corpus/full.json` and `corpus/errors.json`
through the plain, uninstrumented package (no AST hook), with `LINE` and `BRANCH` events on.

What is counted
  statement  a Python statement that owns at least one line with bytecode. Compound statements
             (`if`, `for`, `def`, ...) own their header lines only, so a body statement is its own
             unit. Docstrings and `pass`-only compiled-away lines are not statements. A statement is
             covered when any line it owns ran. (The module is imported with monitoring already on,
             so the module-level `def`, `class` and table statements count as run.)
  line arc   every conditional jump in the bytecode (`POP_JUMP_IF_*`, `FOR_ITER`, `SEND`) has two
             outcomes. A "line arc" is the pair (line of the jump, line it lands on) for an outcome
             that lands on a different line: what coverage.py reports as a branch, except that a
             multi-line condition counts each of its operands as a jump. Covered when the outcome ran.
  outcome    every outcome of every conditional jump, including those that stay on one line
             (`a if c else b`, `x and y`, `any(...)`): the strictest of the three. A jump the compiler
             emits twice (a `while` condition is tested at the top and at the bottom) counts twice.

The report is by function (statements, covered, the uncovered line numbers) and by file. For each
statement the first case id that ran it is recorded, because a location is disabled after its first
hit: the first-hit table says which category of the corpus reaches what.
"""

from __future__ import annotations

import argparse
import ast
import dis
import json
import sys
import time
import types as pytypes
from collections import defaultdict
from pathlib import Path
from typing import Any

import _bootstrap

HERE = _bootstrap.HERE
PKG = _bootstrap.PKG
TARGET_FILES = ("character.py", "skeleton.py", "colorutil.py", "presets.py", "urlstate.py", "attribution.py")
COND_OPS = {"POP_JUMP_IF_FALSE", "POP_JUMP_IF_TRUE", "POP_JUMP_IF_NONE", "POP_JUMP_IF_NOT_NONE", "FOR_ITER", "SEND"}
SKIP_AFTER_TARGET = {"END_FOR", "POP_TOP"}
OUT = HERE / "out" / "coverage-full.json"

mon = sys.monitoring
TOOL = mon.COVERAGE_ID


# --------------------------------------------------------------------------
# static side: statements, branches, functions
# --------------------------------------------------------------------------
class FileInfo:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.name = path.name
        self.source = path.read_text(encoding="utf-8")
        self.lines = self.source.splitlines()
        self.tree = ast.parse(self.source, str(path))
        self.module_code = compile(self.source, str(path), "exec", dont_inherit=True)
        self.code_lines: set[int] = set()
        self.codes: list[pytypes.CodeType] = []
        self._collect(self.module_code)
        # statements: id -> (first line, own lines, function qualname, kind)
        self.statements: list[dict[str, Any]] = []
        self._statements(self.tree, [], None)
        # branches: key -> info
        self.branches: dict[tuple[Any, ...], dict[str, Any]] = {}
        for code in self.codes:
            self._branches(code)

    def _collect(self, code: pytypes.CodeType) -> None:
        self.codes.append(code)
        for _s, _e, line in code.co_lines():
            if line is not None:
                self.code_lines.add(line)
        for c in code.co_consts:
            if isinstance(c, pytypes.CodeType):
                self._collect(c)

    def _statements(self, node: ast.AST, scope: list[str], parent: ast.AST | None) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                self._add_statement(child, scope)
                inner = scope
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                    inner = [*scope, child.name]
                self._statements(child, inner, node)
            else:
                self._statements(child, scope, node)

    def _add_statement(self, node: ast.stmt, scope: list[str]) -> None:
        start = node.lineno
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) and node.decorator_list:
            start = min(d.lineno for d in node.decorator_list)
        body_nodes: list[ast.stmt] = []
        for attr in ("body", "orelse", "finalbody", "handlers", "cases"):
            v = getattr(node, attr, None)
            if isinstance(v, list):
                body_nodes += [x for x in v if isinstance(x, ast.stmt)]
        end = node.end_lineno or node.lineno
        if body_nodes:
            first_child = min(b.lineno for b in body_nodes)
            end = max(start, first_child - 1)
        own = {ln for ln in range(start, end + 1) if ln in self.code_lines}
        if isinstance(node, ast.ExceptHandler):  # pragma: no cover (handled as stmt children)
            return
        if not own:
            return
        self.statements.append(
            {
                "line": node.lineno,
                "own": sorted(own),
                "func": ".".join(scope) if scope else "<module>",
                "kind": type(node).__name__,
            }
        )

    def _expr_text(self, ins: list[dis.Instruction], n: int) -> str:
        """The operand a jump tests, as source text: the position of the instruction that computed
        it (a jump's own position spans the whole `and`/`or` chain), one line at most."""
        k = n - 1
        while k > 0 and ins[k].opname in ("COPY", "TO_BOOL", "NOP", "CACHE"):
            k -= 1
        pos = ins[k].positions if k >= 0 else None
        if pos is None or pos.lineno is None or pos.col_offset is None:
            return ""
        raw = self.lines[pos.lineno - 1].encode("utf-8")
        end = pos.end_col_offset if pos.end_lineno == pos.lineno and pos.end_col_offset is not None else len(raw)
        return raw[pos.col_offset : end].decode("utf-8", errors="replace").strip()[:70]

    def _branches(self, code: pytypes.CodeType) -> None:
        ins = list(dis.get_instructions(code))
        by_off = {i.offset: n for n, i in enumerate(ins)}

        def line_at(off: int) -> int | None:
            n = by_off.get(off)
            while n is not None and n < len(ins):
                pos = ins[n].positions
                if pos and pos.lineno is not None:
                    return pos.lineno
                n += 1
            return None

        def resolve(target: int) -> int:
            n = by_off[target]
            while ins[n].opname in SKIP_AFTER_TARGET and n + 1 < len(ins):
                n += 1
            return ins[n].offset

        for n, i in enumerate(ins):
            if i.opname not in COND_OPS or n + 1 >= len(ins):
                continue
            src = i.positions.lineno if i.positions and i.positions.lineno is not None else None
            fall = ins[n + 1].offset
            if i.opname == "SEND":
                target = i.argval
            else:
                target = i.argval
            if not isinstance(target, int) or target not in by_off:
                continue
            jump_dest = resolve(target) if i.opname == "FOR_ITER" else target
            expr = self._expr_text(ins, n)
            for outcome, dest in (("fall", fall), ("jump", jump_dest)):
                key = (code.co_qualname, code.co_firstlineno, len(code.co_code), i.offset, outcome)
                self.branches[key] = {
                    "func": code.co_qualname,
                    "offset": i.offset,
                    "outcome": outcome,
                    "src": src,
                    "dst": line_at(dest),
                    "op": i.opname,
                    "expr": expr,
                }


# --------------------------------------------------------------------------
# dynamic side
# --------------------------------------------------------------------------
class Collector:
    def __init__(self, files: dict[str, FileInfo]) -> None:
        self.files = files  # by absolute path string
        self.hit_lines: dict[str, dict[int, str]] = {p: {} for p in files}
        self.hit_branches: dict[str, dict[tuple[Any, ...], str]] = {p: {} for p in files}
        self.current = "<import>"
        self._seen_outcomes: dict[tuple[int, int], set[str]] = {}
        self._code_info: dict[int, tuple[pytypes.CodeType, dict[int, int], tuple[Any, ...]]] = {}

    def on_line(self, code: pytypes.CodeType, line: int) -> Any:
        fn = code.co_filename
        hits = self.hit_lines.get(fn)
        if hits is None:
            return mon.DISABLE
        if line not in hits:
            hits[line] = self.current
        return mon.DISABLE

    def on_branch(self, code: pytypes.CodeType, off: int, dest: int) -> Any:
        fn = code.co_filename
        hits = self.hit_branches.get(fn)
        if hits is None:
            return mon.DISABLE
        cid = id(code)
        info = self._code_info.get(cid)
        if info is None:
            fall = {}
            ins = list(dis.get_instructions(code))
            for n, i in enumerate(ins[:-1]):
                fall[i.offset] = ins[n + 1].offset
            info = (code, fall, (code.co_qualname, code.co_firstlineno, len(code.co_code)))
            self._code_info[cid] = info
        _, fall, ckey = info
        outcome = "fall" if fall.get(off) == dest else "jump"
        key = (*ckey, off, outcome)
        if key not in hits:
            hits[key] = self.current
        seen = self._seen_outcomes.setdefault((cid, off), set())
        seen.add(outcome)
        if len(seen) == 2:
            return mon.DISABLE
        return None

    def start(self) -> None:
        mon.use_tool_id(TOOL, "coverage_gate")
        mon.register_callback(TOOL, mon.events.LINE, self.on_line)
        mon.register_callback(TOOL, mon.events.BRANCH, self.on_branch)
        mon.set_events(TOOL, mon.events.LINE | mon.events.BRANCH)

    def stop(self) -> None:
        mon.set_events(TOOL, 0)
        mon.free_tool_id(TOOL)


def run_cases(col: Collector, entries: list[dict[str, Any]], errs: list[dict[str, Any]], limit: int | None, api: bool = True) -> dict[str, Any]:
    import corpus_full as cf
    from anime_character_creator.character import render_character

    n = 0
    t0 = time.time()
    timing: list[tuple[float, str]] = []
    for e in entries:
        if limit is not None and n >= limit:
            break
        col.current = e["id"]
        t1 = time.perf_counter()
        render_character(e["_p"] if "_p" in e else cf.load_full_case(e), **e["kw"])
        timing.append((time.perf_counter() - t1, e["id"]))
        n += 1
    for e in errs:
        col.current = e["id"]
        if e["op"] == "render":
            try:
                render_character(cf.load_full_case(e), **e["kw"])
            except Exception:
                pass
        else:
            cf.run_url_op(e)
        n += 1
    if api:
        # Calls outside render_character that the corpus cannot express: it stores the params an
        # expression produced, not the expression. Labelled "api" in the first-hit table.
        from anime_character_creator import presets

        col.current = "api"
        for ex in presets.EXPRESSIONS.values():
            ex.applied_to(presets.PRESETS["satoko"])
        presets.aged(presets.PRESETS["chiyo"].face, 0.5)
    timing.sort(reverse=True)
    return {"cases": n, "seconds": round(time.time() - t0, 1), "slowest": [[round(s, 3), c] for s, c in timing[:5]]}


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------
def report(files: dict[str, FileInfo], col: Collector) -> dict[str, Any]:
    out: dict[str, Any] = {"files": {}}
    for path, fi in files.items():
        hit_lines = col.hit_lines[path]
        funcs: dict[str, dict[str, Any]] = {}
        uncovered: list[dict[str, Any]] = []
        covered_n = 0
        first_by_func: dict[str, dict[str, int]] = defaultdict(dict)
        for st in fi.statements:
            f = funcs.setdefault(st["func"], {"statements": 0, "covered": 0, "uncovered_lines": []})
            f["statements"] += 1
            ran = [ln for ln in st["own"] if ln in hit_lines]
            if ran:
                f["covered"] += 1
                covered_n += 1
                who = hit_lines[ran[0]]
                first_by_func[st["func"]][who] = first_by_func[st["func"]].get(who, 0) + 1
            else:
                f["uncovered_lines"].append(st["line"])
                uncovered.append(st)
        for fn, d in funcs.items():
            d["first_cases"] = dict(sorted(first_by_func[fn].items(), key=lambda kv: -kv[1])[:6])
        # branches
        hit_b = col.hit_branches[path]
        arcs: dict[tuple[int | None, int | None], bool] = {}
        outcomes_total = 0
        outcomes_hit = 0
        unc_outcomes: list[dict[str, Any]] = []
        for key, b in fi.branches.items():
            outcomes_total += 1
            hit = key in hit_b
            outcomes_hit += hit
            if not hit:
                unc_outcomes.append(b)
            if b["src"] is not None and b["dst"] is not None and b["src"] != b["dst"]:
                a = (b["src"], b["dst"])
                arcs[a] = arcs.get(a, False) or hit
        unc_arcs = sorted(a for a, h in arcs.items() if not h)
        total_st = len(fi.statements)
        out["files"][fi.name] = {
            "statements": total_st,
            "covered": covered_n,
            "percent": round(100.0 * covered_n / total_st, 2) if total_st else 100.0,
            "line_arcs": len(arcs),
            "line_arcs_hit": len(arcs) - len(unc_arcs),
            "line_arc_percent": round(100.0 * (len(arcs) - len(unc_arcs)) / len(arcs), 2) if arcs else 100.0,
            "outcomes": outcomes_total,
            "outcomes_hit": outcomes_hit,
            "outcome_percent": round(100.0 * outcomes_hit / outcomes_total, 2) if outcomes_total else 100.0,
            "raw_lines": len(fi.lines),
            "functions": funcs,
            "uncovered_statements": [{"line": s["line"], "func": s["func"], "kind": s["kind"], "text": fi.lines[s["line"] - 1].strip()[:110]} for s in sorted(uncovered, key=lambda s: s["line"])],
            "uncovered_line_arcs": [[a, b, fi.lines[a - 1].strip()[:90]] for a, b in unc_arcs],
            "uncovered_outcomes": [
                {"func": b["func"], "src": b["src"], "dst": b["dst"], "outcome": b["outcome"], "op": b["op"], "expr": b["expr"], "text": fi.lines[b["src"] - 1].strip()[:90] if b["src"] else ""}
                for b in sorted(unc_outcomes, key=lambda b: (b["src"] or 0, b["offset"]))
            ],
        }
    return out


def print_summary(rep: dict[str, Any]) -> None:
    print(f"{'file':16} {'raw lines':>9} {'stmts':>6} {'covered':>7} {'stmt %':>7} {'line arcs':>10} {'arc %':>7} {'outcomes':>9} {'outc %':>7}")
    for name, f in rep["files"].items():
        print(
            f"{name:16} {f['raw_lines']:>9} {f['statements']:>6} {f['covered']:>7} {f['percent']:>7.2f} {f['line_arcs_hit']:>4}/{f['line_arcs']:<5} {f['line_arc_percent']:>7.2f} {f['outcomes_hit']:>4}/{f['outcomes']:<4} {f['outcome_percent']:>7.2f}"
        )


def probes(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure the facts that make the remaining uncovered statements dead code: wrap a few
    private functions, run the whole corpus, and report what their arguments ever were."""
    import ast as _ast
    import math

    import corpus_full as cf
    from anime_character_creator import character as ch

    res: dict[str, Any] = {}
    # _interp and _interp_flat: how close a value ever comes to either end of the knots
    m = {"lo": math.inf, "hi": math.inf, "calls": 0, "flat_lo": math.inf, "flat_hi": math.inf}
    orig_interp, orig_flat = ch._interp, ch._interp_flat

    def w_interp(v: float, xs: Any, ys: Any) -> float:
        m["calls"] += 1
        m["lo"] = min(m["lo"], v - xs[0])
        m["hi"] = min(m["hi"], xs[-1] - v)
        return orig_interp(v, xs, ys)

    def w_flat(v: float, xs: Any, ys: Any) -> float:
        m["flat_lo"] = min(m["flat_lo"], v - xs[0])
        m["flat_hi"] = min(m["flat_hi"], xs[-1] - v)
        return orig_flat(v, xs, ys)

    # _lock_shape: the shortest span, and the fewest sample points inside the span
    ls = {"min_span": math.inf, "min_points": math.inf, "calls": 0}
    orig_lock = ch._lock_shape

    def w_lock(cx: float, cy: float, r: float, points: Any, width: float, t0: float = 0.0, t1: float = 1.0, power: float = 0.75, offset: float = 0.0) -> str:
        ls["calls"] += 1
        ls["min_span"] = min(ls["min_span"], t1 - t0)
        n = len(ch._lock_line(points))
        inside = sum(1 for i in range(n) if t0 <= i / (n - 1) <= t1)
        ls["min_points"] = min(ls["min_points"], inside)
        return orig_lock(cx, cy, r, points, width, t0, t1, power, offset)

    # _hair_tip_lines: the shortest tip line in pixels
    tl = {"min_len": math.inf, "calls": 0}
    orig_tips = ch._hair_tip_lines

    def w_tips(sk: Any, tips: Any) -> str:
        tl["calls"] += 1
        for (ax, ay), (ex, ey) in tips:
            tl["min_len"] = min(tl["min_len"], math.hypot((ex - ax) * sk.head_r, (ey - ay) * sk.head_r))
        return orig_tips(sk, tips)

    # _chain_until_y: does the chain ever end above y (so the loop runs out without a split)?
    cu = {"calls": 0, "ran_out": 0}
    orig_chain = ch._chain_until_y

    def w_chain(chain: Any, y: float) -> Any:
        cu["calls"] += 1
        if all(e[1] <= y for _c, e in chain[1]):
            cu["ran_out"] += 1
        return orig_chain(chain, y)

    # _eye_lash, _hand_centre, _traced_placement: arguments
    lash = {"calls": 0, "reach_none": 0}
    orig_lash = ch._eye_lash

    def w_lash(er: float, f: Any, edge_w: float, reach: float | None = None) -> Any:
        lash["calls"] += 1
        lash["reach_none"] += reach is None
        return orig_lash(er, f, edge_w, reach)

    sides = {"hand_centre": set(), "traced_placement": set()}
    orig_hc, orig_tp = ch._hand_centre, ch._traced_placement

    def w_hc(sk: Any, p: Any, s: int) -> Any:
        sides["hand_centre"].add(s)
        return orig_hc(sk, p, s)

    def w_tp(sk: Any, p: Any, side: int) -> Any:
        sides["traced_placement"].add(side)
        return orig_tp(sk, p, side)

    ch._interp, ch._interp_flat, ch._lock_shape, ch._hair_tip_lines = w_interp, w_flat, w_lock, w_tips
    ch._chain_until_y, ch._eye_lash, ch._hand_centre, ch._traced_placement = w_chain, w_lash, w_hc, w_tp
    try:
        for e in entries:
            ch.render_character(cf.load_full_case(e), **e["kw"])
    finally:
        ch._interp, ch._interp_flat, ch._lock_shape, ch._hair_tip_lines = orig_interp, orig_flat, orig_lock, orig_tips
        ch._chain_until_y, ch._eye_lash, ch._hand_centre, ch._traced_placement = orig_chain, orig_lash, orig_hc, orig_tp
    res["interp"] = {"calls": m["calls"], "min_v_minus_first_knot": m["lo"], "min_last_knot_minus_v": m["hi"], "flat_min_v_minus_first": m["flat_lo"], "flat_min_last_minus_v": m["flat_hi"]}
    res["lock_shape"] = ls
    res["hair_tip_lines"] = tl
    res["chain_until_y"] = cu
    res["eye_lash"] = lash
    res["sides"] = {k: sorted(v) for k, v in sides.items()}
    # data and constants, read from the module
    src = (PKG / "character.py").read_text(encoding="utf-8")
    tree = _ast.parse(src)
    defs: dict[str, list[int]] = defaultdict(list)
    for n in tree.body:
        if isinstance(n, _ast.FunctionDef):
            defs[n.name].append(n.lineno)
    res["functions_defined_twice"] = {k: v for k, v in defs.items() if len(v) > 1}
    res["_BEARD_LIP_W"] = ch._BEARD_LIP_W
    res["_COAT_BUST_BOW"] = ch._COAT_BUST_BOW
    res["_HAIR_CHEEK_Y"] = ch._HAIR_CHEEK_Y
    styles = {}
    for name, st in ch.HAIRSTYLES.items():
        roles = set()
        if st.locks is not None:
            for fall in (0.8, 1.2, 1.8, 2.4, 3.0):
                roles |= {lk[0] for lk in st.locks(fall)}
        styles[name] = {"strands": st.strands is not None, "front_shade": st.front_shade is not None, "underside": st.underside is not None, "locks": st.locks is not None, "mass_locks": bool(st.mass_locks), "tip_lines": st.tip_lines is not None, "lock_roles": sorted(roles)}
    res["hairstyles"] = styles
    # _belt_drawn: show_tie is never true while show_buckle is
    combos = []
    for apron_none in (True, False):
        for obi in (True, False):
            show_buckle = apron_none and not obi
            show_tie = not show_buckle or not apron_none
            combos.append({"apron_none": apron_none, "obi": obi, "show_buckle": show_buckle, "show_tie": show_tie})
    res["belt_truth_table"] = combos
    res["belt_both_shown"] = any(c["show_buckle"] and c["show_tie"] for c in combos)
    return res


CORPUS_DIR = HERE / "corpus"


def load_corpus() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ok = json.loads((CORPUS_DIR / "full.json").read_text(encoding="utf-8"))
    errs = json.loads((CORPUS_DIR / "errors.json").read_text(encoding="utf-8"))
    return ok, errs


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--limit", type=int, default=None)
    r.add_argument("--only", default="", help="comma separated id prefixes (category names) to run")
    r.add_argument("--dir", default=None, help="a directory holding full.json and errors.json (default corpus/)")
    r.add_argument("--skip", default="", help="comma separated id prefixes (category names) to leave out")
    r.add_argument("--min", type=float, default=98.0, help="fail below this percent of character.py statements")
    r.add_argument("--out", default=str(OUT))
    r.add_argument("--corpus", choices=("full", "mini"), default="full", help="mini: the 68 cases of corpus/mini.json, for comparison")
    r.add_argument("--no-api", action="store_true", help="skip the Expression.applied_to and presets.aged calls")
    sub.add_parser("probes")
    s = sub.add_parser("show")
    s.add_argument("target")
    args = ap.parse_args(argv[1:])
    if sys.version_info < (3, 12):
        print("needs CPython 3.12+ (sys.monitoring)")
        return 2
    files = {str((PKG / n).resolve()): FileInfo(PKG / n) for n in TARGET_FILES}
    if args.cmd == "show":
        name, _, func = args.target.partition(":")
        fi = next(f for f in files.values() if f.name == name)
        rep = json.loads(Path(OUT).read_text(encoding="utf-8"))
        for u in rep["files"][name]["uncovered_statements"]:
            if u["func"] == func:
                print(u["line"], fi.lines[u["line"] - 1])
        return 0
    global CORPUS_DIR
    if getattr(args, "dir", None):
        CORPUS_DIR = Path(args.dir)
    ok, errs = load_corpus()
    if args.cmd == "run" and args.corpus == "mini":
        raw = json.loads((HERE / "corpus" / "mini.json").read_text(encoding="utf-8"))
        ok = [{"id": c["id"], "kw": c["kwargs"], "_p": None, "_params": c["params"]} for c in raw]
        errs = []
    if args.cmd == "probes":
        import pprint

        pprint.pprint(probes(ok), width=140, sort_dicts=False)
        return 0
    if args.only:
        pre = tuple(p + "-" for p in args.only.split(","))
        ok = [e for e in ok if e["id"].startswith(pre)]
        errs = [e for e in errs if e["id"].startswith(pre)]
    if args.skip:
        skip = tuple(p + "-" for p in args.skip.split(","))
        ok = [e for e in ok if not e["id"].startswith(skip)]
        errs = [e for e in errs if not e["id"].startswith(skip)]
    col = Collector(files)
    col.start()
    try:
        import corpus_full  # noqa: F401  (imports the package lazily, with monitoring on)

        _bootstrap.assert_package_location()
        import anime_character_creator  # noqa: F401
        from anime_character_creator import attribution, colorutil, presets, skeleton, urlstate  # noqa: F401

        if args.cmd == "run" and args.corpus == "mini":
            import cases as mini_cases

            for e in ok:
                e["_p"] = mini_cases.params_from_dict(e["_params"])
        stats = run_cases(col, ok, errs, args.limit, not args.no_api)
    finally:
        col.stop()
    rep = report(files, col)
    rep["run"] = {**stats, "python": sys.version.split()[0], "ok_cases": len(ok), "error_cases": len(errs)}
    Path(args.out).parent.mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(rep, indent=1, sort_keys=True), encoding="utf-8")
    print(f"ran {stats['cases']} cases in {stats['seconds']} s; slowest {stats['slowest'][:3]}")
    print_summary(rep)
    pct = rep["files"]["character.py"]["percent"]
    print(f"character.py statements covered: {pct:.2f}% (gate {args.min}%)")
    return 0 if pct >= args.min else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
