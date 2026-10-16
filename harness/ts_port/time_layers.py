"""Wall time of the UNinstrumented Python renderer over the mini corpus.

    time_layers.py [--reps N]    (default 5; one warm-up call first, median reported)

Per case: median ms of a full render_character. Per layer: the source expression of
every element of `chest`, `under_arms` and `layers` is pulled out of character.py with
ast (no import hook) and evaluated on its own against the module globals with `sk`, `p`
and the already built `chest` / `under_arms` lists in scope, so each layer's own cost is
timed in isolation (median of N after one warm-up). Writes out/time-python.json.
"""

from __future__ import annotations

import ast
import json
import statistics
import sys
import time
from typing import Any

import _bootstrap


def layer_exprs() -> dict[str, str]:
    src = (_bootstrap.PKG / "character.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "render_character")
    out: dict[str, str] = {}
    for stmt in fn.body:
        if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name):
            name = stmt.targets[0].id
            if name in ("chest", "under_arms", "layers") and isinstance(stmt.value, ast.List):
                for i, e in enumerate(stmt.value.elts):
                    if not isinstance(e, ast.Starred):
                        out[f"{name}[{i}]"] = ast.get_source_segment(src, e) or ""
    return out


def median_ms(fn: Any, reps: int) -> float:
    fn()
    times = []
    for _ in range(reps):
        t = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t) * 1000)
    return statistics.median(times)


def p95(xs: list[float]) -> float:
    s = sorted(xs)
    return s[min(len(s) - 1, round(0.95 * (len(s) - 1) + 0.4999))]


def main(argv: list[str]) -> int:
    reps = int(argv[argv.index("--reps") + 1]) if "--reps" in argv else 5
    from anime_character_creator import character
    from anime_character_creator.character import render_character, skeleton_for

    import cases

    _bootstrap.assert_package_location()
    if "__stage" in render_character.__code__.co_names:
        raise RuntimeError("timing must run uninstrumented")
    exprs = layer_exprs()
    code = {k: compile(v, f"<{k}>", "eval") for k, v in exprs.items()}
    g = vars(character)
    result: dict[str, Any] = {"python": sys.version.split()[0], "reps": reps, "cases": {}}
    for c in cases.load_cases():
        p, kw = c["p"], c["kwargs"]
        total = median_ms(lambda p=p, kw=kw: render_character(p, **kw), reps)
        sk = skeleton_for(p)
        env: dict[str, Any] = {"sk": sk, "p": p, "chest": [], "under_arms": []}
        layers: dict[str, float] = {}
        for name, co in code.items():
            val: list[str] = []

            def run(co: Any = co, val: list[str] = val) -> None:
                val[:] = [eval(co, g, env)]

            layers[name] = median_ms(run, reps)
            if name.startswith("chest["):
                env["chest"].append(val[0])
            elif name.startswith("under_arms["):
                env["under_arms"].append(val[0])
        result["cases"][c["id"]] = {"finish": p.finish, "total_ms": total, "layers_ms": layers}
    out = _bootstrap.HERE / "out" / "time-python.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=1), encoding="utf-8")

    print(f"python {result['python']}, median of {reps} after 1 warm-up, ms")
    print(f"{'finish':8}{'cases':>6}{'mean':>9}{'median':>9}{'p95':>9}{'max':>9}")
    for finish in ("flat", "soft"):
        xs = [v["total_ms"] for v in result["cases"].values() if v["finish"] == finish]
        print(f"{finish:8}{len(xs):>6}{statistics.mean(xs):>9.2f}{statistics.median(xs):>9.2f}{p95(xs):>9.2f}{max(xs):>9.2f}")
    print("\nslowest layers, median over cases of per-case median ms (flat / soft)")
    names = list(exprs)
    rows = []
    for n in names:
        f = statistics.median(v["layers_ms"][n] for v in result["cases"].values() if v["finish"] == "flat")
        s = statistics.median(v["layers_ms"][n] for v in result["cases"].values() if v["finish"] == "soft")
        rows.append((max(f, s), n, f, s))
    for _, n, f, s in sorted(rows, reverse=True)[:10]:
        print(f"{n:16}{f:>9.3f}{s:>9.3f}   {exprs[n][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
