"""The head's outline (sin, cos, a fractional power, then `.1f`) over random geometries: the end-to-end test of whether
maths-library ulp differences ever change a printed digit. Writes `ts/fixtures/headshape-sweep.json`:
a list of [build, cx, cy, r, sha256[:20] of the path text].

    PY harness/ts_port/headshape_sweep.py [N]
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

from anime_character_creator.character import _curve, _head_shape  # noqa: E402

_bootstrap.assert_package_location()
OUT = Path(__file__).resolve().parents[2] / "ts" / "fixtures" / "headshape-sweep.json"


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    rng = random.Random(99)
    rows = []
    for _ in range(n):
        build = rng.choice([0.0, 0.1, 1.0, rng.random(), rng.random(), rng.uniform(0, 1.3)])
        cx, cy, r = 200.0, rng.uniform(30, 220), rng.uniform(20, 120)
        d = _curve(cx, cy, r, *_head_shape(build))
        rows.append([build, cx, cy, r, hashlib.sha256(d.encode()).hexdigest()[:20]])
    OUT.write_text(json.dumps(rows, separators=(",", ":")))
    print(OUT, OUT.stat().st_size, len(rows))


if __name__ == "__main__":
    main()
