"""Differential fuzzing: random characters nobody designed, drawn by the frozen Python and recorded for the TypeScript to match.

    PY harness/ts_port/fuzz.py [N] [SEED]        writes harness/ts_port/out/fuzz-<SEED>.json (gitignored)
    node ts/tools/fuzz-check.ts <that file>      renders every case in TypeScript and compares

Uses the corpus generator's `random_drawer` (every field from pools of in-range, extreme and out-of-range values) with a seed
the corpus does not use, more fields per case and heavier weights on the extremes. Each case records the sha256 prefix of the
document, or the exception class if Python raises. The documents themselves are not kept.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import random
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

import corpus_full as cf  # noqa: E402

_bootstrap.assert_package_location()
OUT = Path(__file__).resolve().parent / "out"
ODD_PREFIXES = ["p", "a$&b", "x\\1", "é", "a.b", "", "\\g<1>z", "<x>"]
BACKGROUNDS = ["white", "#fff", "url(#g)", "red", "", None]


def one(entry: dict) -> dict:
    from anime_character_creator.character import render_character

    try:
        svg = render_character(cf.load_full_case(entry), **entry["kw"])
    except Exception as e:
        return {"exc": type(e).__name__}
    return {"doc": hashlib.sha256(svg.encode("utf-8", "surrogatepass")).hexdigest()[:20]}


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 777
    t = cf.types()
    rnd = random.Random(seed)
    base = cf.bases(t)
    kit = cf.kitted(t)
    # in-range, extreme and out-of-range weights; FUZZ_WEIGHTS="0.2,0.2,0.6" leans on the out-of-range values
    w = tuple(float(x) for x in os.environ.get("FUZZ_WEIGHTS", "0.35,0.30,0.35").split(","))
    draw = cf.random_drawer(t, base, kit, rnd, fields_per_case=(2, 20), weights=(w[0], w[1], w[2]), from_presets=0.2)
    entries = []
    for i in range(n):
        p = draw()
        kw: dict = {}
        r = rnd.random()
        if r < 0.10:
            kw["id_prefix"] = rnd.choice(ODD_PREFIXES)
        elif r < 0.15:
            kw["background"] = rnd.choice(BACKGROUNDS)
        elif r < 0.18:
            kw["metadata"] = True
        entries.append(cf.entry_of(t, f"fz{seed}-{i:05d}", p, kw))
    with multiprocessing.get_context("fork").Pool(8) as pool:
        results = pool.map(one, entries, chunksize=64)
    for e, r in zip(entries, results, strict=True):
        e.update(r)
    OUT.mkdir(exist_ok=True)
    path = OUT / f"fuzz-{seed}.json"
    path.write_text(cf.dumps_compact(entries))
    raised = sum(1 for r in results if "exc" in r)
    print(f"{path}: {n} cases, {raised} raise ({100 * raised / n:.1f}%)")


if __name__ == "__main__":
    main()
