"""D1 of `docs/detail-plan.md`: did the line-weight change touch only the ink?

Compares two `harness/tall_chibi/snapshot.py` runs, before and after:

1. With every `stroke-width` attribute stripped, each SVG must be identical,
   except the filled lines whose width is their geometry (the bust fold, the
   bare breasts' line, the male chest lines), which are listed.
2. Every stroke's new width against its old one, element by element: the
   ratios should cluster at 0.75 (outlines), 0.55 (interior lines) and 1 (the
   `<mask>` widening and the goggles' rim, kept), off only by the `.1f`
   rounding of both.

    ./harness/run.sh harness/detail/d1_check.py out/detail/d1_before out/detail/d1_after
"""

import collections
import os
import re
import sys

SW = re.compile(r'stroke-width="([0-9.]+)"')
ELEMENT = re.compile(r"<[a-zA-Z][^>]*>")


def main() -> None:
    before, after = sys.argv[1], sys.argv[2]
    ratios: collections.Counter = collections.Counter()
    geometry: collections.Counter = collections.Counter()
    for name in sorted(os.listdir(before)):
        a = open(os.path.join(before, name)).read()
        b = open(os.path.join(after, name)).read()
        ea, eb = ELEMENT.findall(a), ELEMENT.findall(b)
        if len(ea) != len(eb):
            print(f"{name}: element count {len(ea)} -> {len(eb)}")
            continue
        for x, y in zip(ea, eb):
            if SW.sub("", x) != SW.sub("", y):
                geometry[(name.split(".")[0] if name.count(".") > 1 else name, x[:40])] += 1
                continue
            wa, wb = SW.findall(x), SW.findall(y)
            for u, v in zip(wa, wb):
                u, v = float(u), float(v)
                if u:
                    ratios[round(v / u, 2)] += 1
    print("elements whose geometry changed:")
    shapes = collections.Counter(k[1] for k in geometry.elements())
    for shape, n in shapes.most_common():
        print(f"  {n:5d}  {shape}")
    print("stroke ratios (new / old), rounded:")
    for r in sorted(ratios):
        print(f"  {r:5.2f}  {ratios[r]}")


if __name__ == "__main__":
    main()
