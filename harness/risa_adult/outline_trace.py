"""Fit the face and hair-silhouette masks of outline_masks.py into chains in head radii, and emit them as TypeScript.

    ./harness/run.sh harness/risa_adult/outline_masks.py
    ./harness/run.sh harness/risa_adult/outline_trace.py

The fitting is harness/franzi_hair/outline_trace.py's (copied, since that file runs on import), at the same calibration (origin x 660,
origin y 270.5, 175.7 reference px per head radius: Risa's head sits where Franzi's does). Writes out/risa_adult/outline.json and
ts/src/body-adult-risa-data.ts.

Where a chain sits relative to the edge matters, because the stroke is drawn centred on it:
    face, strips, ears   the reference draws a black line just outside the skin, so the chain is grown 2 px onto that line's centre
    sil (hair)           the hair has no drawn line, only its own edge, so the chain is shrunk 1 px: the stroke's outer edge, not its
                         centre, then lands on the edge (the stroke is about 2.5 px wide)
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, ".claude/skills/trace-reference")
sys.path.insert(0, "harness/risa_adult")
import trace_lib as tl  # noqa: E402

OX, OY, S = 660.0, 270.5, 175.7
TOL = 0.01
m = np.load("out/risa_adult/outline_masks.npz")


def to_r(pts):
    return [((x - OX) / S, (y - OY) / S) for x, y in pts]


def components(mask, min_px):
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        c = lab == i
        if c.sum() >= min_px:
            out.append(c)
    return sorted(out, key=lambda c: -c.sum())


def fit(mask, grow, blur, tol=TOL, min_px=40):
    """The closed chains of every component of `mask`, grown (or, negative, shrunk) by `grow` px and smoothed."""
    f = ndimage.gaussian_filter(mask.astype(float), blur) if blur else mask.astype(float)
    # growing the edge by g px is a threshold of Phi(-g / sigma) on the blurred field (Phi the normal CDF), and shrinking it the same
    # with the sign turned; with no blur the threshold stays at one half
    level = 0.5 * (1 + math.erf(-grow / (blur * math.sqrt(2)))) if blur else 0.5
    out = []
    for c in components(f > level, min_px):
        out.append(tl.fit_closed(to_r(tl.boundary(c)), tol))
    return out


SIL_SIGMA_HI, SIL_SIGMA_LO, SIL_STEP, SIL_KEEP = 7.0, 2.0, 7.0, 2.5


def find_tips(pts, win=7, min_turn=105.0, min_sep=20):
    """Indices of the sharp convex tips of a closed contour: where the edge turns back by more than `min_turn` degrees over +-win px."""
    n = len(pts)
    sm = np.stack([ndimage.gaussian_filter1d(pts[:, j], 1.2, mode="wrap") for j in (0, 1)], 1)
    a, b = sm - np.roll(sm, win, axis=0), np.roll(sm, -win, axis=0) - sm
    area = 0.5 * np.sum(sm[:, 0] * np.roll(sm[:, 1], -1) - np.roll(sm[:, 0], -1) * sm[:, 1])
    # signed turn, positive where the edge bends the same way the contour winds (a convex tip), negative in a notch
    turn = np.degrees(np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0], (a * b).sum(1))) * np.sign(area)
    cand = [i for i in range(n) if turn[i] > min_turn and turn[i] >= turn[np.arange(i - win, i + win + 1) % n].max()]
    out = []
    for i in sorted(cand, key=lambda i: -turn[i]):
        if all(min(abs(i - j), n - abs(i - j)) > min_sep for j in out):
            out.append(i)
    return sorted(out)


def fit_smooth(mask, shift=-1, min_px=150, sigma_hi=None, step=None, keep_tips=False, keep=None, lo=None):
    """Closed chains whose slope is continuous at every join, for the hair silhouette.

    The hair's edge is the edge of an AI segmentation: ragged at the pixel scale, and fitted with the least number of quadratics that
    stay within 2 px it came out as 90 short curves meeting at kinks (81 of 89 joins over 10 degrees), which reads as wobble. Here the
    edge is low-passed along its length (sigma SIL_SIGMA_HI px), except where that would move it more than SIL_KEEP px off the real
    edge: there a tip or a narrow lock is being rounded off, so the light smoothing (SIL_SIGMA_LO) is blended in (full below 1.5 px of
    movement, none above SIL_KEEP + 1.5). The result is resampled every SIL_STEP px and drawn as a quadratic B-spline: the curve runs
    through the midpoints of the polygon's sides with each vertex as a control point, so the slope cannot jump at a join.
    """
    sig_hi = sigma_hi or SIL_SIGMA_HI
    out = []
    if shift < 0:
        # The shrink puts the stroke's outer edge on the hair edge, but on a part only a few px wide it eats half the width and shortens the
        # tip (the ponytail's wisp is 4 px wide and ran out 15 px early). Parts narrower than a disc of radius 2 are kept as they are.
        disc = np.hypot(*np.mgrid[-2:3, -2:3]) <= 2
        thin = mask & ~ndimage.binary_opening(mask, structure=disc)
        moved = ndimage.binary_erosion(mask, iterations=-shift) | thin
    else:
        moved = ndimage.binary_dilation(mask, iterations=shift) if shift > 0 else mask
    for c in components(moved, min_px):
        pts = np.array(tl.boundary(c), float)
        n = len(pts)
        tree = cKDTree(pts)

        def smooth(sig):
            return np.stack([ndimage.gaussian_filter1d(pts[:, j], sig, mode="wrap") for j in (0, 1)], 1)

        hi, lo_ = smooth(sig_hi), smooth(lo or SIL_SIGMA_LO)
        d = tree.query(hi)[0]
        w = np.clip((d - (keep if keep is not None else SIL_KEEP) + 1.5) / 3.0, 0, 1)[:, None]  # 0 where the smooth edge is within SIL_KEEP - 1.5 px of the real one
        sm = (1 - w) * hi + w * lo_
        seg = np.hypot(*np.diff(np.vstack([sm, sm[:1]]), axis=0).T)
        arc = np.concatenate([[0], np.cumsum(seg)])
        m = max(8, int(round(arc[-1] / (step or SIL_STEP))))
        t = np.linspace(0, arc[-1], m, endpoint=False)
        tips = find_tips(pts) if keep_tips else []
        for i in tips:  # a vertex exactly on each real tip, twice, so the spline reaches it (a doubled control point is a corner)
            t = t[np.abs(t - arc[i]) > 3.0]
            t = np.sort(np.concatenate([t, [arc[i], arc[i]]]))
        sm = sm.copy()
        for i in tips:
            sm[i] = pts[i]
        if tips:
            print("    tips kept at", [tuple(int(v) for v in pts[i]) for i in tips])
        verts = np.stack([np.interp(t, arc, np.append(sm[:, j], sm[0, j])) for j in (0, 1)], 1)
        q = np.array(to_r([tuple(v) for v in verts]))
        mid = (q + np.roll(q, -1, axis=0)) / 2
        start = tuple(mid[0])
        segs = [(tuple(q[(i + 1) % m]), tuple(mid[(i + 1) % m])) for i in range(m)]
        out.append((start, segs))
        print(f"  smooth chain: {n} edge px, {m} vertices, max smooth-vs-real edge distance {tree.query(sm)[0].max():.1f} px")
    return out


NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def longest_paths(mask, min_len):
    """Ordered (x, y) polylines of a thin mask: in each 8-connected piece the longest path, then the longest of what is left, while at least min_len px."""
    from collections import deque

    out = []
    todo = [[(int(y), int(x)) for y, x in zip(*np.nonzero(mask))]]
    lab_, k = ndimage.label(mask, structure=np.ones((3, 3)))
    todo = [[(int(y), int(x)) for y, x in zip(*np.nonzero(lab_ == i))] for i in range(1, k + 1)]
    while todo:
        px = todo.pop()
        if len(px) < min_len:
            continue
        S_ = set(px)

        def bfs(src):
            par, dist, q = {src: None}, {src: 0}, deque([src])
            last = src
            while q:
                u = q.popleft()
                last = u
                for dy, dx in NB:
                    v = (u[0] + dy, u[1] + dx)
                    if v in S_ and v not in par:
                        par[v], dist[v] = u, dist[u] + 1
                        q.append(v)
            return last, par

        a, _ = bfs(px[0])
        b, par = bfs(a)
        path = []
        while b is not None:
            path.append(b)
            b = par[b]
        if len(path) >= min_len:
            out.append([(x, y) for y, x in path])
        halo = {(y + dy, x + dx) for y, x in path for dy in (-1, 0, 1) for dx in (-1, 0, 1)}
        rest = [p for p in px if p not in halo]
        if rest:
            sub = np.zeros(mask.shape, bool)
            for y, x in rest:
                sub[y, x] = True
            lab2, k2 = ndimage.label(sub, structure=np.ones((3, 3)))
            todo.extend([[(int(y), int(x)) for y, x in zip(*np.nonzero(lab2 == i))] for i in range(1, k2 + 1)])
    return out


def fringe_data():
    """The fringe's hair as closed shapes (each with the real tips and slits) and the thin edge lines where it meets skin, with their widths in head radii."""
    shapes = [tl.fit_closed(to_r(tl.boundary(c)), 0.006) for c in components(m["fringe_hair"], 150)]
    # The edge lines: walk the ordered boundary of the fringe's hair and keep the runs of it that touch skin (within 2 px of a pixel of the domain that is not hair), away from the
    # domain's own border; a gap of up to 3 px inside a run is bridged. Each run is one open line, so the whole edge is drawn, slits and tips included.
    from zones import DOM_BOX

    dom = np.zeros(m["fringe_hair"].shape, bool)
    dom[DOM_BOX[1] : DOM_BOX[3], DOM_BOX[0] : DOM_BOX[2]] = True
    near_skin = ndimage.binary_dilation(dom & ~m["fringe_hair"], iterations=2) & dom
    lines, widths = [], []
    for c in components(m["fringe_hair"], 150):
        ring = tl.boundary(c)
        flag = [bool(near_skin[y, x]) for x, y in ring]
        n = len(ring)
        # start the walk at an unflagged pixel so a run is never split by the start
        try:
            k0 = flag.index(False)
        except ValueError:
            k0 = 0
        order = [(k0 + i) % n for i in range(n)]
        runs, cur, gap = [], [], 0
        for idx in order:
            if flag[idx]:
                cur.append(ring[idx])
                gap = 0
            else:
                gap += 1
                if cur and gap <= 3:
                    cur.append(ring[idx])
                elif cur:
                    runs.append(cur[: len(cur) - (gap - 1)] if gap > 1 else cur)
                    cur = []
        if cur:
            runs.append(cur)
        for run in runs:
            if len(run) < 10:
                continue
            a = np.array(run, float)
            if len(a) > 8:
                a = np.stack([ndimage.gaussian_filter1d(a[:, j], 1.2, mode="nearest") for j in (0, 1)], 1)
            pts = to_r([tuple(v) for v in a[::2]])
            if len(pts) < 3:
                continue
            ch = tl.fit_chain(pts, tl.simplify(pts, 0.004))
            lines.append(ch)
            widths.append([FRINGE_LINE_PX / S] * (1 + len(ch[1])))
    return shapes, lines, widths


FRINGE_LINE_PX = 1.8  # the reference's lock edges are drawn about 1.5 to 2 px wide


res = {
    # the fringe's lower edge is blunt locks with slits between them: the edge keeps its corners wherever the heavy smoothing would move it more than a pixel, and the vertices come every 3 px
    "face": fit_smooth(m["face_ext"], shift=1, min_px=2000, sigma_hi=4.0, step=3.0, keep=1.0, lo=1.2),
    "sil": fit_smooth(m["sil"], shift=-1, keep_tips=True),
}
json.dump(res, open("out/risa_adult/outline.json", "w"), default=lambda o: list(o))
for k, v in res.items():
    print(f"{k:7s} chains {len(v)}  segments {[len(c[1]) for c in v]}")


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


def chain(c):
    st, sg = c
    return f"[{pt(st)}, [{', '.join(f'[{pt(cc)}, {pt(e)}]' for cc, e in sg)}]]"


doc = {
    "face": "The visible skin of Risa's face: under the fringe, cheeks, chin, filled across the eyes. Its edge is the fringe's lower edge, the side locks' inner edges and the jaw.",
    "sil": "Risa's hair silhouette: every visible hair pixel, the face shrunk a few pixels, and the runs of body between hair on both sides, so it runs under the body (her hair hangs behind the shoulders and the arms).",
}
parts = [
    "// Generated by harness/risa_adult/outline_trace.py from outline_masks.py (the regions of ref/risa-adult/00-bikini.png). Do not edit by hand.\n"
    "// Head radii from the head centre, the calibration in harness/franzi_hair/trace.py (175.7 reference px per radius).\n\n"
    'import type { Chain } from "./tables.ts";\n'
]
for key, name in (("face", "RISA_SKIN_FACE"), ("sil", "RISA_HAIR_SILHOUETTE")):
    body = ",\n  ".join(chain(c) for c in res[key])
    parts.append(f"/** {doc[key]} */\nexport const {name}: readonly Chain[] = [\n  {body},\n];\n")
sp = Path("out/risa_adult/strands.json")
if sp.exists():  # strands_auto.py's lines, as chains (run it after outline_masks.py and before this)
    sd = json.load(open(sp))
    body = ",\n  ".join(chain(c) for c in sd["inside"])
    parts.append("/** Risa's strand lines: the dark lines where one lock of hair lies over the next, found by harness/risa_adult/strands_auto.py. They taper out inside the hair. */\n" f"export const RISA_HAIR_STRANDS: readonly Chain[] = [\n  {body},\n];\n")
    body = ",\n  ".join(chain(c) for c in sd["edge"])
    parts.append("/** The lines that run down to the face's edge (the fringe's locks, the side locks): they end on it, the face's skin drawn over what passes it. */\n" f"export const RISA_HAIR_EDGE_STRANDS: readonly Chain[] = [\n  {body},\n];\n")
fh, fl, fw = fringe_data()
body = ",\n  ".join(chain(c) for c in fh)
parts.append("/** The fringe's hair as closed shapes, with the real tips and the slits between the locks: drawn over the skin, which runs up under it. */\n" f"export const RISA_FRINGE_HAIR: readonly Chain[] = [\n  {body},\n];\n")
body = ",\n  ".join(chain(c) for c in fl)
wid = ",\n  ".join("[" + ", ".join(f"{w:.4f}" for w in ws) + "]" for ws in fw)
parts.append("/** The thin lines along the fringe's edge where it meets skin, and their thicknesses in head radii. */\n" f"export const RISA_FRINGE_LINES: readonly Chain[] = [\n  {body},\n];\n")
parts.append(f"export const RISA_FRINGE_LINE_WIDTHS: readonly (readonly number[])[] = [\n  {wid},\n];\n")
print("fringe:", len(fh), "shapes,", len(fl), "edge lines")
bp = Path("out/risa_adult/brows.json")
if bp.exists():  # brows.py's two lines
    b = json.load(open(bp))
    body = ",\n  ".join(chain(c) for c in b["chains"])
    wid = ",\n  ".join("[" + ", ".join(f"{w:.4f}" for w in ws) + "]" for ws in b["widths"])
    parts.append("/** Risa's brows, the viewer's left then right: thin dark lines across the fringe (harness/risa_adult/brows.py). */\n" f"export const RISA_BROWS: readonly Chain[] = [\n  {body},\n];\n")
    parts.append("/** The thickness of each brow at each of its fitted points, in head radii. */\n" f"export const RISA_BROW_WIDTHS: readonly (readonly number[])[] = [\n  {wid},\n];\n")
Path("ts/src/body-adult-risa-data.ts").write_text("\n".join(parts))
print("wrote ts/src/body-adult-risa-data.ts")
