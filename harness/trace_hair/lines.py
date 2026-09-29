"""The reference hair's line work, traced line by line (the trace skill's
interior lines, done on `contrast.py`'s black-hat instead of a darkness
threshold).

The first trace (`trace_hair.py`) took dark pixels (a colour sum at most 120)
inside the hair and ordered each piece along its main axis: it found 16
lines, since most of the reference's lines are only a little darker than the
fill, and a piece that curves or branches comes out as one straight average.
Here:

1. **The black-hat** (`contrast.py`): the grey closing over a disk of radius
   `R`, minus the picture; a line is bright wherever it sits, on sheen or in
   shadow.
2. **Hysteresis**: pixels over `HI` seed a line and those over `LO` touching
   one extend it, so faint ends are kept without taking the fill's texture.
3. **Thinning** to one pixel (Zhang and Suen's, in numpy; scikit-image is not
   a dependency).
4. **Walking** the skeleton: split at junctions, spurs under `SPUR` px
   dropped, each branch an ordered path.
5. **Fitting** each path in head radii (D0's face-width calibration) with
   Douglas-Peucker at `TOL` and a least-squares control per segment.

Lines touching the hair's own edge (within `EDGE` px of the cut) are the
outline, not line work, and are dropped: the silhouette is traced separately.

Writes `out/trace_hair/lines.json` (chains in the reference's head radii, as
traced, unmapped), and `lines_overlay.png` / `lines_zoom.png`: the chains in
colour over the black-hat view.
"""

import json
import sys

sys.path.insert(0, "harness/trace_hair")
sys.path.insert(0, "harness/detail")
sys.path.insert(0, ".claude/skills/trace-reference")

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import baseline
import contrast as ct
import trace_lib as tl

OUT = "out/trace_hair"
R = 4
HI, LO = 18.0, 8.0
SPUR = 6
MIN_LEN = 10
TOL = 0.008
EDGE = 3
EDGE_SHARE = 0.6
GAP = 8.0
TURN = 35.0


def thin(m: np.ndarray) -> np.ndarray:
    """Zhang-Suen thinning."""
    img = np.pad(m.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            P = img
            p2, p3, p4 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:]
            p5, p6, p7 = P[2:, 2:], P[2:, 1:-1], P[2:, :-2]
            p8, p9 = P[1:-1, :-2], P[:-2, :-2]
            nb = [p2, p3, p4, p5, p6, p7, p8, p9]
            B = sum(n.astype(int) for n in nb)
            seq = nb + [p2]
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(int) for i in range(8))
            if step == 0:
                c = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                c = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            core = P[1:-1, 1:-1]
            rm = (core == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if rm.any():
                core[rm] = 0
                changed = True
        if not changed:
            break
    return img[1:-1, 1:-1].astype(bool)


NB8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def paths(sk: np.ndarray) -> list[list[tuple[int, int]]]:
    """The skeleton's branches as ordered (x, y) pixel paths, split at
    junctions, short spurs dropped."""
    k = np.ones((3, 3))
    k[1, 1] = 0
    deg = ndi.convolve(sk.astype(int), k, mode="constant") * sk
    junction = sk & (deg >= 3)
    body = sk & ~junction
    lab, n = ndi.label(body, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        pts = set(zip(ys.tolist(), xs.tolist()))
        if len(pts) < 2:
            continue

        def nbrs(p):
            return [(p[0] + dy, p[1] + dx) for dy, dx in NB8 if (p[0] + dy, p[1] + dx) in pts]

        ends = [p for p in pts if len(nbrs(p)) <= 1]
        start = ends[0] if ends else next(iter(pts))
        path, seen, cur = [start], {start}, start
        while True:
            nx = [q for q in nbrs(cur) if q not in seen]
            if not nx:
                break
            # prefer the 4-neighbour, so a diagonal step does not skip a pixel
            nx.sort(key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
            cur = nx[0]
            seen.add(cur)
            path.append(cur)
        out.append([(float(x), float(y)) for y, x in path])
    return merge(out, junction)


def _end(p, at_start, back=6):
    """An end of a path and its direction of travel out of the path there."""
    k = min(back, len(p) - 1)
    e, q = (p[0], p[k]) if at_start else (p[-1], p[-1 - k])
    d = np.subtract(e, q)
    n = np.hypot(*d) or 1.0
    return np.array(e), d / n


def merge(ps, junction):
    """Carry lines through junctions and across short gaps.

    Each path end next to a junction cluster is extended to the cluster's
    centre. Then, best first, two ends are joined when they head toward each
    other (their directions of travel within `TURN` of opposite) and are
    within `GAP` px, the gap itself lying along both: a crossing's two lines
    come out whole, a line broken by a faint stretch comes out as one.
    """
    jl, nj = ndi.label(junction, structure=np.ones((3, 3)))
    centres = ndi.center_of_mass(junction, jl, range(1, nj + 1)) if nj else []
    for p in ps:
        for at_start in (True, False):
            x, y = p[0] if at_start else p[-1]
            x, y = int(x), int(y)
            hit = {jl[y + dy, x + dx] for dy, dx in NB8 if 0 <= y + dy < jl.shape[0] and 0 <= x + dx < jl.shape[1]} - {0}
            if hit:
                cy, cx = centres[min(hit) - 1]
                if at_start:
                    p.insert(0, (cx, cy))
                else:
                    p.append((cx, cy))
    cos_turn = np.cos(np.radians(TURN))
    while True:
        best = None
        ends = [(i, s, *_end(p, s)) for i, p in enumerate(ps) if len(p) >= 2 for s in (True, False)]
        for a in range(len(ends)):
            i, si, ei, di = ends[a]
            for b in range(a + 1, len(ends)):
                j, sj, ej, dj = ends[b]
                if i == j:
                    continue
                v = ej - ei
                dist = np.hypot(*v)
                if dist > GAP or di @ dj > -cos_turn:
                    continue
                if dist > 2 and (di @ v / dist < cos_turn or -dj @ v / dist < cos_turn):
                    continue
                score = dist - 10 * (-(di @ dj))
                if best is None or score < best[0]:
                    best = (score, i, si, j, sj)
        if best is None:
            return ps
        _, i, si, j, sj = best
        a = ps[i][::-1] if si else ps[i]
        b = ps[j] if sj else ps[j][::-1]
        joined = a + b
        ps = [p for k, p in enumerate(ps) if k not in (i, j)] + [joined]


def main() -> None:
    a = np.asarray(Image.open(ct.REF).convert("RGB")).astype(float)
    lum = a @ np.array([0.299, 0.587, 0.114])
    m = ct.hair_mask(lum.shape)
    disk = np.hypot(*np.mgrid[-R : R + 1, -R : R + 1]) <= R
    bh = ndi.grey_closing(lum, footprint=disk) - lum
    inner = ndi.binary_erosion(m, iterations=1)
    lo = inner & (bh > LO)
    lab, n = ndi.label(lo, structure=np.ones((3, 3)))
    strong = np.unique(lab[inner & (bh > HI)])
    lines = np.isin(lab, strong[strong > 0])
    # One-pixel breaks along a line would split it; a 3x3 closing bridges them.
    lines = ndi.binary_closing(lines, np.ones((3, 3))) & inner
    sk = thin(lines)
    # A path that mostly hugs the cut's edge is the outline, not line work.
    near_edge = m & ~ndi.binary_erosion(m, iterations=EDGE + 1)
    ps = [p for p in paths(sk) if len(p) >= MIN_LEN and np.mean([near_edge[int(y), int(x)] for x, y in p]) < EDGE_SHARE]

    cal: list[str] = []
    ox, oy, s = baseline.calibrate(cal)
    chains = []
    for p in ps:
        u = [((x - ox) / s, (y - oy) / s) for x, y in p]
        chains.append(tl.fit_chain(u, tl.simplify(u, TOL)))
    json.dump({"calibration": {"origin": [ox, oy], "px_per_r": s}, "lines": chains}, open(f"{OUT}/lines.json", "w"), indent=1)
    print(f"line px {int(lines.sum())}, skeleton px {int(sk.sum())}, paths {len(ps)}, segments {sum(len(c[1]) for c in chains)}")

    view = np.where(m, np.clip(255 - bh * 2.5, 150, 255), 120).astype(np.uint8)
    rng = np.random.default_rng(4)
    for name, (x0, y0, x1, y1), k in (("lines_overlay", ct.CROP, 2), ("lines_zoom", (440, 200, 600, 420), 5)):
        im = Image.fromarray(view[y0:y1, x0:x1]).convert("RGB").resize(((x1 - x0) * k, (y1 - y0) * k), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d_done = []
        for ch in chains:
            col = [(230, 20, 20), (20, 150, 230), (20, 170, 40), (220, 120, 0), (170, 0, 200)][len(d_done) % 5]
            d_done.append(1)
            pts = [((ox + q[0] * s - x0) * k, (oy + q[1] * s - y0) * k) for q in tl.sample_chain(*ch)]
            d.line(pts, fill=col, width=max(2, k // 2 + 1))
        im.save(f"{OUT}/{name}.png")
        print(f"{OUT}/{name}.png", im.size)


if __name__ == "__main__":
    main()
