"""What the Risa trace scripts share (`docs/risa-plan.md`).

The composite and the segments are placed at the offsets `crops.py` verified, and
coordinates are converted into the **cut frame**: head radii on
`character.BODY_TYPES["tall_slender"]`, which is the reference's own 165 px per
head radius under the profile's 0.85 head scale (`_SLENDER_HEAD_SCALE`), with the
head centre at her chin minus 1.02 of that radius. A cut traced in that frame is
the identity on the body it was traced on, which is what `GarmentCut.ref_body`
says.

Importing this runs no measurement and prints nothing.
"""

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

BASE = "ref-local/mio"

SKULL_R = 165.0
HEAD_SCALE = 0.85
R = SKULL_R * HEAD_SCALE
CHIN = 399
CX = 630.0
CY = CHIN - 1.02 * R

OFFSETS = {
    "anime-girl.png": (416, 47),
    "school-blazer.png": (440, 410),
    "white-collared-shirt.png": (447, 401),
    "pleated-skirt.png": (475, 836),
    "blue-ribbon.png": (593, 435),
    "brown-loafers/brown-loafers-1.png": (531, 1388),
    "brown-loafers/brown-loafers-2.png": (650, 1388),
    "long-black-hair.png": (417, 47),
    "bangs.png": (511, 101),
}

_comp = np.asarray(Image.open(f"{BASE}/mio.png").convert("RGBA")).astype(int)
H, W = _comp.shape[:2]
_alpha = _comp[:, :, 3:4] / 255.0
RGB = (_comp[:, :, :3] * _alpha + 255 * (1 - _alpha)).astype(int)


def hy(y):
    return (y - CY) / R


def hx(x):
    return (x - CX) / R


def segment(name):
    """`(alpha mask, rgb)` of a segment placed on the composite's canvas."""
    ox, oy = OFFSETS[name]
    seg = np.asarray(Image.open(f"{BASE}/segments/{name}").convert("RGBA")).astype(int)
    sh, sw = seg.shape[:2]
    mask = np.zeros((H, W), bool)
    rgb = np.zeros((H, W, 3), int)
    mask[oy : oy + sh, ox : ox + sw] = seg[:, :, 3] > 128
    rgb[oy : oy + sh, ox : ox + sw] = seg[:, :, :3]
    return mask, rgb


def median_colour(mask, rgb=RGB, erode=2):
    inner = ndi.binary_erosion(mask, iterations=erode)
    px = rgb[inner if inner.any() else mask]
    return "#%02x%02x%02x" % tuple(int(v) for v in np.median(px, axis=0))


def thin(mask):
    """Zhang-Suen thinning: a one-pixel-wide skeleton of `mask`.

    scipy has no skeletonize and scikit-image is not a dependency; the masks here
    are a few hundred pixels, so the plain iterative form is plenty.
    """
    img = np.pad(mask.astype(np.uint8), 1)
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            p = img
            n = [
                p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:], p[2:, 2:],
                p[2:, 1:-1], p[2:, :-2], p[1:-1, :-2], p[:-2, :-2],
            ]  # fmt: skip
            c = p[1:-1, 1:-1]
            b = sum(n)
            a = sum(((n[i] == 0) & (n[(i + 1) % 8] == 1)).astype(np.uint8) for i in range(8))
            if step == 0:
                cond = (n[0] * n[2] * n[4] == 0) & (n[2] * n[4] * n[6] == 0)
            else:
                cond = (n[0] * n[2] * n[6] == 0) & (n[0] * n[4] * n[6] == 0)
            kill = (c == 1) & (b >= 2) & (b <= 6) & (a == 1) & cond
            if kill.any():
                changed = True
                img[1:-1, 1:-1][kill] = 0
    return img[1:-1, 1:-1].astype(bool)


def walk(skel):
    """The ordered pixel path along a thinned line, from one end to the other.

    Starts at an endpoint (a pixel with one neighbour) and follows neighbours,
    preferring the unvisited one that continues straight. A closed or branching
    skeleton is walked as far as it goes, which is what an open stroke needs.
    """
    pts = {tuple(p) for p in np.argwhere(skel)}
    if not pts:
        return []

    def nbrs(p):
        y, x = p
        return [
            (y + dy, x + dx)
            for dy in (-1, 0, 1)
            for dx in (-1, 0, 1)
            if (dy or dx) and (y + dy, x + dx) in pts
        ]

    ends = [p for p in pts if len(nbrs(p)) == 1]
    ring = not ends
    start = min(ends) if ends else min(pts)
    path, seen = [start], {start}
    cur = start
    while True:
        cand = [q for q in nbrs(cur) if q not in seen]
        if not cand:
            break
        if len(path) >= 2:
            d = (cur[0] - path[-2][0], cur[1] - path[-2][1])
            cand.sort(key=lambda q: -((q[0] - cur[0]) * d[0] + (q[1] - cur[1]) * d[1]))
        else:
            cand.sort(key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
        cur = cand[0]
        path.append(cur)
        seen.add(cur)
    if ring and abs(cur[0] - start[0]) <= 1 and abs(cur[1] - start[1]) <= 1:
        path.append(start)  # a closed loop comes back to where it began
    return [(x, y) for y, x in path]


def branches(skel, min_len=6):
    """The strokes of a branching skeleton, each walked end to end.

    A network of fold lines (the ribbon's) has junctions, which `walk` cannot
    follow. Taking the junction pixels out leaves one clean stroke per branch;
    the one-to-three pixel gap at each junction is under the stroke's own width.
    """
    pts = {tuple(p) for p in np.argwhere(skel)}

    def count(p):
        y, x = p
        return sum((y + dy, x + dx) in pts for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)

    junctions = {p for p in pts if count(p) >= 3}
    # A junction is a small blob, not one pixel: take its neighbours too.
    cut = set(junctions)
    for y, x in junctions:
        cut.update((y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    rest = np.zeros_like(skel)
    for y, x in pts - cut:
        rest[y, x] = True
    lab, n = ndi.label(rest, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        path = walk(lab == i)
        if len(path) >= min_len:
            out.append(path)
    return out


def prune(skel, spur=8, rounds=3):
    """The skeleton without its spurs: branches shorter than `spur` pixels that end at a
    free end and join the rest at a junction. Zhang-Suen thinning sprouts one wherever
    a stroke's edge is rough, and each spur is a junction that splits a long line in two;
    taking them off first is what lets a hair's whole strand come out as one stroke."""
    skel = skel.copy()
    for _ in range(rounds):
        pts = {tuple(p) for p in np.argwhere(skel)}

        def nbrs(p):
            y, x = p
            return [
                (y + dy, x + dx)
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dy or dx) and (y + dy, x + dx) in pts
            ]

        ends = [p for p in pts if len(nbrs(p)) == 1]
        removed = False
        for e in ends:
            path, seen, cur = [e], {e}, e
            while True:
                nxt = [q for q in nbrs(cur) if q not in seen]
                if len(nxt) != 1:
                    break  # a junction (or a dead end) ahead
                cur = nxt[0]
                if len(nbrs(cur)) >= 3:
                    break
                path.append(cur)
                seen.add(cur)
                if len(path) > spur:
                    break
            if len(path) <= spur and len(nbrs(cur)) >= 3:
                for q in path:
                    skel[q] = False
                removed = True
        if not removed:
            break
    return skel


def strokes_of(skel, min_len=12):
    """The strokes of a skeleton, cut at its junctions (`branches` without the gap a
    neighbourhood cut leaves): only the junction pixels themselves are taken out."""
    pts = {tuple(p) for p in np.argwhere(skel)}

    def count(p):
        y, x = p
        return sum((y + dy, x + dx) in pts for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)

    rest = np.zeros_like(skel)
    for p in pts:
        if count(p) < 3:
            rest[p] = True
    lab, n = ndi.label(rest, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        path = walk(lab == i)
        if len(path) >= min_len:
            out.append(path)
    return out
