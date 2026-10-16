"""Synthetic adversarial fixtures for the TypeScript kernel (`ts/src/pynum.ts`).

    PYTHONPATH=src PY harness/ts_port/synthetic.py [--large]

Writes `ts/fixtures/synthetic.json` (committed, small) and with --large also
`harness/ts_port/out/synthetic-large.json` (ignored). Every expected value is what CPython computes here, so
the TS side is tested against Python itself and not against a belief about it.

Values are encoded as in `record.py`: "f:" + 16 hex digits of the big-endian IEEE-754 double, "i:" + decimal,
"s:" + text. Errors are {"err": "ValueError", "msg": "..."}.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness" / "ts_port"))
import _bootstrap  # noqa: E402,F401


def f(x: float) -> str:
    return "f:" + struct.pack(">d", x).hex()


def i(n: int) -> str:
    return f"i:{n}"


def err(e: Exception) -> dict:
    return {"err": type(e).__name__, "msg": str(e)}


def next_up(x: float) -> float:
    return math.nextafter(x, math.inf)


def next_down(x: float) -> float:
    return math.nextafter(x, -math.inf)


def float_pool(rng: random.Random, n: int) -> list[float]:
    """Values chosen to hurt: ties at every precision, neighbours of ties, zeros, tiny, huge, specials."""
    out: list[float] = [0.0, -0.0, math.inf, -math.inf, math.nan, 1e21, -1e21, 1e22, 1e300, 5e-324, 2.2250738585072014e-308]
    for m in range(0, 14):  # exact binary ties: k / 2**m
        for k in range(-40, 41):
            out.append(k / 2**m)
    for d in range(0, 4):  # decimal half points that are NOT binary ties (0.15, 0.35, ...)
        for k in range(0, 200):
            out.append((k + 0.5) / 10**d)
            out.append(k / 10**d + 0.5 / 10 ** (d + 0))
    base = list(out)
    for x in base:
        if math.isfinite(x):
            out.append(next_up(x))
            out.append(next_down(x))
    while len(out) < n:
        mode = rng.random()
        if mode < 0.4:
            out.append(rng.uniform(-1000, 1000))
        elif mode < 0.6:
            out.append(round(rng.uniform(-500, 500), rng.randint(0, 4)))
        elif mode < 0.8:
            out.append(rng.uniform(-1, 1) * 10 ** rng.randint(-8, 8))
        else:
            out.append(struct.unpack(">d", struct.pack(">Q", rng.getrandbits(64)))[0])
    return out[:n] if n < len(out) else out


def build(large: bool) -> dict:
    rng = random.Random(20261016)
    pool = float_pool(rng, 60000 if large else 6000)
    fx: dict = {}

    fx["fmt"] = []
    for x in pool:
        for d in (0, 1, 2, 3) if large else (1, 2):
            fx["fmt"].append([f(x), d, format(x, f".{d}f")])

    fx["hex2"] = [[n, format(n, "02x")] for n in list(range(0, 256))]

    fx["round"] = []
    for x in pool:
        try:
            fx["round"].append([f(x), i(round(x))])
        except Exception as e:  # nan, inf
            fx["round"].append([f(x), err(e)])

    fx["roundTo"] = []
    for x in pool:
        for n in (1, 2, 3, 4) if large else (2, 3):
            fx["roundTo"].append([f(x), n, f(round(x, n))])

    fx["repr"] = []
    for x in pool:
        fx["repr"].append([f(x), repr(x)])

    fx["mod"] = []
    divisors = [1.0, 4.0, -4.0, 0.3, 7.0, 124.0, 6.0, 1e-3, math.pi]
    for x in pool[: (12000 if large else 500)]:
        for b in divisors:
            try:
                fx["mod"].append([f(x), f(b), f(x % b)])
            except Exception as e:
                fx["mod"].append([f(x), f(b), err(e)])

    fx["modInt"] = [[a, b, i(a % b)] for a in range(-30, 31) for b in (1, 2, 3, 4, 6, 7, 124)]

    fx["sum"] = []
    finite = [x for x in pool if math.isfinite(x) and abs(x) < 1e100]
    for _ in range(4000 if large else 800):
        n = rng.randint(1, 12)
        items = [rng.choice(finite) if rng.random() < 0.3 else rng.uniform(-300, 300) for _ in range(n)]
        lead = rng.randint(0, min(n, 3)) if rng.random() < 0.25 else 0
        py_items: list = [int(round(v)) if k < lead else v for k, v in enumerate(items)]
        ints = [int(round(v)) for v in items[:lead]]
        fx["sum"].append([[f(v) if k >= lead else i(int(py_items[k])) for k, v in enumerate(items)], lead, f(float(sum(py_items)))])
    fx["sum"].append([[f(0.1)] * 10, 0, f(sum([0.1] * 10))])
    fx["sum"].append([[f(1e100), f(1.0), f(-1e100)], 0, f(sum([1e100, 1.0, -1e100]))])

    fx["hypot"] = []
    for _ in range(40000 if large else 4000):
        s = 10.0 ** rng.randint(-6, 6)
        a, b = rng.uniform(-1, 1) * s, rng.uniform(-1, 1) * s
        fx["hypot"].append([f(a), f(b), f(math.hypot(a, b))])
    for a, b in [(0.1, 0.7), (3.0, 4.0), (0.0, 0.0), (-0.0, 0.0), (1e-320, 1e-320), (1e300, 1e300), (math.inf, math.nan), (math.nan, 1.0)]:
        fx["hypot"].append([f(a), f(b), f(math.hypot(a, b))])

    fx["slice"] = []
    base_list = list(range(10))
    for start in [None, 0, 1, 3, -1, -3, -20, 20, 9, 10, 11]:
        for stop in [None, 0, 1, 5, -1, -4, -20, 20, 10]:
            for step in [1, 2, -1, -2, 3, -3]:
                fx["slice"].append([base_list, start, stop, step, base_list[start:stop:step]])

    fx["at"] = [[base_list, k, (base_list[k] if -10 <= k < 10 else {"err": "IndexError"})] for k in range(-12, 12)]

    fx["sha1"] = []
    for s in ["", "a", "abc", "x" * 55, "x" * 56, "x" * 64, "x" * 119, "M10.0 20.5 L3 4", "é日本語😀", "breasts-test"] + [
        "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789 .,-MLCQZ") for _ in range(rng.randint(0, 300))) for _ in range(200)
    ]:
        fx["sha1"].append([s, hashlib.sha1(s.encode()).hexdigest()])

    # re.sub with a template built from a prefix, as _namespace_ids does
    body = 'a <g id="hair-front"> <use href="#hair-front"/> <path clip-path="url(#hair-front)"/> id="x" </g>'
    fx["template"] = []
    prefixes = ["p", "a$&b", "x\\1", "x\\\\y", "q\\n", "\\g<1>z", "k\\2", "bad\\q", "é", "\\0", "\\12", "\\101", "tail\\", "\\g<0>", "\\g<x>", "a.b", "$1"]
    for pre in prefixes:
        try:
            r = re.sub(r'\bid="([^"]+)"', rf'id="{pre}-\1"', body)
            r = re.sub(r"url\(#([^)]+)\)", rf"url(#{pre}-\1)", r)
            r = re.sub(r'href="#([^"]+)"', rf'href="#{pre}-\1"', r)
            fx["template"].append([body, pre, r])
        except Exception as e:
            fx["template"].append([body, pre, err(e)])

    fx["pyFloat"] = []
    for s in ["1", "1.", ".5", "0.66", "1e3", " 2.5 ", "+3", "-.5", "1_0", "", ".", "1.2.3", "abc", "1e", "inf", "nan", "٣"]:
        try:
            fx["pyFloat"].append([s, f(float(s))])
        except Exception as e:
            fx["pyFloat"].append([s, err(e)])

    fx["pyHex"] = []
    for s in ["00", "ff", "FF", "0d", "7", "", "g1", "+f", " f", "0x", "1_", "f f"]:
        try:
            fx["pyHex"].append([s, i(int(s, 16))])
        except Exception as e:
            fx["pyHex"].append([s, err(e)])

    # x ** y: CPython's special cases and error classes; ordinary results compared within one ulp (the engine's pow)
    fx["pow"] = []
    xs = [0.0, -0.0, 1.0, -1.0, 2.0, -2.0, 0.5, -0.5, 3.0, 10.0, 1e-300, 1e300, 0.3, math.inf, -math.inf, math.nan, 7.0, -8.0]
    ys = [0.0, -0.0, 1.0, 2.0, 3.0, -1.0, -2.0, 0.5, -0.5, 1.4, -1.4, 2.5, 1e5, -1e5, 1e300, math.inf, -math.inf, math.nan, 5.0, -3.0]
    for x in xs:
        for yv in ys:
            try:
                r = x**yv
                fx["pow"].append([f(x), f(yv), {"err": "complex"} if isinstance(r, complex) else f(r)])
            except Exception as e:
                fx["pow"].append([f(x), f(yv), err(e)])
    for _ in range(3000 if large else 600):
        x, yv = rng.uniform(0, 3), rng.choice([1.4, 2.0, 0.5, 3.0, -1.0, rng.uniform(-4, 4)])
        fx["pow"].append([f(x), f(yv), f(x**yv)])

    fx["hexfull"] = []
    for t in ["00", "ff", "FF", "7", "", "g1", "+f", "-1", "-0", " f", "f ", "\tf\n", "\u00a0f", "\u2003f", "\u00851", "f_f", "1__2", "_1", "1_", "0x1f", "0X_f", "0x", "0x_", "+", "-", "0b1", "٣f", "١٢", "１２", "𝟏𝟐", "1٣", "f" * 13, "0" * 20 + "f", "a b", "1.5", "ｆ"]:
        try:
            fx["hexfull"].append([t, i(int(t, 16))])
        except Exception as e:
            fx["hexfull"].append([t, err(e)])

    fx["hexfmt"] = [[n, format(n, "02x")] for n in (-255, -16, -15, -1, 0, 5, 15, 16, 255)]
    fx["replaceEmpty"] = [[t, r, t.replace("", r)] for t, r in (("abc", "-"), ("", "-"), ("a😀b", "+"), ("x", "$&"))]
    fx["sortStr"] = [
        [["\uffff", "\U0001f600", "a", "\ue000", "\U00010000", "Z", "é", ""], sorted(["\uffff", "\U0001f600", "a", "\ue000", "\U00010000", "Z", "é", ""])],
        [["b", "a", "B", "aa", "a1", "10", "9"], sorted(["b", "a", "B", "aa", "a1", "10", "9"])],
    ]

    fx["sorted"] = [
        [[f(10.2), f(9.5), f(100.0), f(-3.0)], [f(x) for x in sorted([10.2, 9.5, 100.0, -3.0])]],
        [[i(10), i(9), i(100), i(2)], [i(x) for x in sorted([10, 9, 100, 2])]],
    ]
    return fx


def main() -> None:
    large = "--large" in sys.argv
    fx = build(large)
    dest = ROOT / ("harness/ts_port/out/synthetic-large.json" if large else "ts/fixtures/synthetic.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(fx, separators=(",", ":"), ensure_ascii=True))
    print(dest, dest.stat().st_size, {k: len(v) for k, v in fx.items()})


if __name__ == "__main__":
    main()
