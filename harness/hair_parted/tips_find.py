"""The tips of the traced cut, for the line that runs on past each one (the
owner, after step 5: the reference "has a hairline after the edge", which
makes the tips look natural).

At each lock's tip the reference's two side lines meet and carry on as one
stroke tapering to nothing, 0.09 to 0.16 head radii past where its colour, and
so our trace, stops (measured where it shows, on the front locks over the
jacket; over the black page line and page are one colour). Ours stopped at the
colour with a round join of the full outline, a blunt end.

A tip here is an anchor where the chain turns back on itself, the two sides
meeting at under `ANGLE` degrees (62: the fitted tangents put real tips at 26
to 59), and the corner points out of the hair: a step along the bisector
from it lands outside the region the chain bounds (the mass for the
silhouette, the front for the lock edges and hairline). Tips are taken on the
mass edge (the outer falls' points, drawn behind the body) and on the front's
hairline and lock edges (drawn over it), and at four joins, where a tip is
two chains' ends: each front lock's lowest point (the hairline meets the
lock's edge) and each outer fall's lowest point (the silhouette's end meets
the fall's inner edge).

Each tip is written as its apex and a unit direction, the bisector, in head
radii. Writes `out/hair_parted/tips.json` and `tips_found.png`.

    ./harness/run.sh harness/hair_parted/tips_find.py
"""

import json
import math
import sys

sys.path.insert(0, "harness/hair_parted")
sys.path.insert(0, ".claude/skills/trace-reference")

import numpy as np
from PIL import Image, ImageDraw

import regions as R
import trace_lib as tl

OUT = "out/hair_parted"
ANGLE = 62.0


def unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n)


def tangents(chain):
    """Per anchor: the unit direction leaving it backward (toward the previous
    control) and forward (toward the next control), None at the ends."""
    start, segs = chain
    anchors = [start, *(e for _, e in segs)]
    out = []
    for i, a in enumerate(anchors):
        back = unit((segs[i - 1][0][0] - a[0], segs[i - 1][0][1] - a[1])) if i > 0 else None
        fwd = unit((segs[i][0][0] - a[0], segs[i][0][1] - a[1])) if i < len(segs) else None
        out.append((a, back, fwd))
    return out


def corner(a, u1, u2, mask, cal):
    """A tip, as (apex, direction), if the corner at `a` between leaving
    directions `u1` and `u2` is sharp and points out of `mask`; else None."""
    cos = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
    if math.degrees(math.acos(cos)) >= ANGLE:
        return None
    d = unit((-(u1[0] + u2[0]), -(u1[1] + u2[1])))
    ox, oy, s = cal
    x, y = ox + (a[0] + d[0] * 0.03) * s, oy + (a[1] + d[1] * 0.03) * s
    if mask[int(round(y)), int(round(x))]:
        return None
    return (a, d)


def main() -> None:
    t = json.load(open(f"{OUT}/trace.json"))
    z = np.load(f"{OUT}/regions.npz")
    mass, front = z["mass"], z["front"]
    cal = tuple(z["cal"])
    behind, ahead = [], []
    # The silhouette: interior anchors only (its two ends meet the closing
    # chord behind the body).
    for a, b, f in tangents(t["mass"])[1:-1]:
        hit = corner(a, b, f, mass, cal)
        if hit:
            behind.append(hit)
    # The front: interior anchors of the hairline and the lock edges, and the
    # two joins where the hairline's ends meet the lock edges' ends.
    for key in ("line", "lock_l", "lock_r"):
        for a, b, f in tangents(t[key])[1:-1]:
            hit = corner(a, b, f, front, cal)
            if hit:
                ahead.append(hit)
    line = tangents(t["line"])
    for lock, end in (("lock_l", line[0]), ("lock_r", line[-1])):
        a, _, f_line = end if end[2] else (end[0], None, end[1])
        lt = tangents(t[lock])[-1]
        hit = corner(a, f_line, lt[1], front, cal)
        if hit:
            ahead.append(hit)
    # Each outer fall's lowest point: the silhouette's first and last anchors,
    # where it meets the fall's inner edge (whose last anchor is the same point).
    mt = tangents(t["mass"])
    for end, under in ((mt[0], "under_l"), (mt[-1], "under_r")):
        a = end[0]
        u_mass = end[2] if end[2] else end[1]
        ut = tangents(t[under])[-1]
        hit = corner(a, u_mass, ut[1], mass, cal)
        if hit:
            behind.append(hit)
    print(f"{len(behind)} tips on the silhouette, {len(ahead)} on the front")
    for name, tips in (("behind", behind), ("front", ahead)):
        for a, d in tips:
            print(f"  {name}: ({a[0]:+.3f}, {a[1]:+.3f}) toward ({d[0]:+.2f}, {d[1]:+.2f})")
    json.dump({"behind": behind, "front": ahead}, open(f"{OUT}/tips.json", "w"), indent=1)

    comp = np.asarray(Image.open(f"{R.REF}/katherina_grok_nohat.png").convert("RGB")).astype(float)
    im = Image.fromarray(np.clip(comp * 2.4, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    ox, oy, s = cal
    for k in ("mass", "line", "lock_l", "lock_r"):
        d.line([(ox + x * s, oy + y * s) for x, y in tl.sample_chain(*t[k], per_segment=16)], fill=(255, 255, 255), width=1)
    for tips, col in ((behind, (0, 255, 255)), (ahead, (255, 200, 0))):
        for (x, y), (dx, dy) in tips:
            px, py = ox + x * s, oy + y * s
            d.ellipse([px - 4, py - 4, px + 4, py + 4], outline=col, width=2)
            d.line([(px, py), (px + dx * 0.15 * s, py + dy * 0.15 * s)], fill=col, width=2)
    im.crop((330, 180, 1000, 1000)).save(f"{OUT}/tips_found.png")
    print(f"{OUT}/tips_found.png")


if __name__ == "__main__":
    main()
