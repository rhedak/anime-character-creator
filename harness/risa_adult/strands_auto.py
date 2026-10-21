"""Risa's strand lines, found by a ridge detector on the reference's hair and fitted as chains in head radii.

    ./harness/run.sh harness/risa_adult/outline_masks.py          # first: out/risa_adult/outline_masks.npz
    ./harness/run.sh harness/risa_adult/strands_auto.py [view X0 Y0 X1 Y1 [ZOOM]]

Her hair has dozens of fine dark lines where one strand group lies over the next, too many to read off a grid one by one the way
harness/franzi_hair/strands3.py did for Franzi's dozen. A dark line is a valley of the luminance, so: the Hessian of the luminance at
SIGMA px, the valleys where its larger eigenvalue passes THRESH_HI and runs on while it stays over THRESH_LO (hysteresis), thinned by
non-maximum suppression across the line, then each connected piece is walked into ordered polylines (the longest path, removed, then
what is left of it, down to MIN_LEN px), smoothed along their length and simplified into quadratic chains.

Only the dark lines are taken; the pale gloss bands across the crown are not lines and stay out of the flat style.
`view` writes out/risa_adult/strands-view.png (the reference of the box with the lines over it); the bare run writes
out/risa_adult/strands.json (chains for emit_strands.py).
"""

import json
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OX, OY, S = 660.0, 270.5, 175.7
SIGMA = 1.3
THRESH_HI = 9.0
THRESH_LO = 4.5
MIN_LEN = 22  # px
FZ_LO, FZ_HI = 9.0, 16.0  # the fringe's thresholds, on the local-contrast view
SMOOTH = 3.0  # px, along the line
SIMPLIFY = 0.010  # head radii

img = np.array(Image.open("ref/risa-adult/00-bikini.png").convert("RGB")).astype(float)
lum = img.mean(2)
m = np.load("out/risa_adult/outline_masks.npz")
hair_in = ndimage.binary_erosion(m["hair"], iterations=4)

gy = lambda v, o: ndimage.gaussian_filter(v, SIGMA, order=o)  # noqa: E731
Lxx, Lyy, Lxy = gy(lum, (0, 2)), gy(lum, (2, 0)), gy(lum, (1, 1))
tr, det = Lxx + Lyy, Lxx * Lyy - Lxy**2
disc = np.sqrt(np.maximum(tr**2 / 4 - det, 0))
lam = tr / 2 + disc  # the larger eigenvalue: positive across a dark line
# the unit vector across the line: the eigenvector of `lam`
nx, ny = Lxy, lam - Lxx
norm = np.maximum(np.hypot(nx, ny), 1e-9)
nx, ny = nx / norm, ny / norm
resp = lam * SIGMA**2
H, W = lum.shape
yy, xx = np.mgrid[0:H, 0:W].astype(float)
up = ndimage.map_coordinates(resp, [yy + ny, xx + nx], order=1)
dn = ndimage.map_coordinates(resp, [yy - ny, xx - nx], order=1)
nms = (resp >= up) & (resp >= dn)
cand = nms & (resp > THRESH_LO) & hair_in
lab, n = ndimage.label(cand, structure=np.ones((3, 3)))
keep = np.zeros(n + 1, bool)
strong = ndimage.maximum(resp, lab, range(1, n + 1))
keep[1:] = np.asarray(strong) > THRESH_HI
ridge = keep[lab] & cand

# The fringe's locks are separated by many thin lines that run down to the lock tips, dark red on red, too faint for the global threshold. In the fringe's box the
# detector runs on the luminance with its local contrast stretched (the luminance minus its blur over the local spread, as harness/franzi_hair/contrast.py's C), where those
# lines are as strong as any, and the hair mask is kept to within 1 px of its edge so a line can reach the tips (the face's skin is drawn over what passes the edge).
FZ = (572, 195, 748, 312)  # x0, y0, x1, y1 in reference px
fz = np.zeros(lum.shape, bool)
fz[FZ[1] : FZ[3], FZ[0] : FZ[2]] = True
mu_ = ndimage.gaussian_filter(lum, 6)
sd_ = np.sqrt(ndimage.gaussian_filter((lum - mu_) ** 2, 6)) + 3.0
Cc = 100.0 * (lum - mu_) / sd_
cxx, cyy, cxy = (ndimage.gaussian_filter(Cc, 1.2, order=o) for o in ((0, 2), (2, 0), (1, 1)))
ctr, cdet = cxx + cyy, cxx * cyy - cxy**2
clam = ctr / 2 + np.sqrt(np.maximum(ctr**2 / 4 - cdet, 0))
cnx, cny = cxy, clam - cxx
cn = np.maximum(np.hypot(cnx, cny), 1e-9)
cnx, cny = cnx / cn, cny / cn
cresp = clam * 1.2**2
cup = ndimage.map_coordinates(cresp, [yy + cny, xx + cnx], order=1)
cdn = ndimage.map_coordinates(cresp, [yy - cny, xx - cnx], order=1)
sys.path.insert(0, "harness/risa_adult")
from zones import EYES_MASK, brow_mask  # noqa: E402

# the lock tips go on as thin dark lines past the hair's fill into the skin: lines are looked for up to 8 px past the hair's edge, but not along the brows or the eyes' edges
hair_edge = ndimage.binary_dilation(m["hair"], iterations=8) & ~brow_mask(11) & ~EYES_MASK
cand_f = (cresp >= cup) & (cresp >= cdn) & (cresp > FZ_LO) & hair_edge & fz & (lum < mu_ - 3)
lab_f, nf = ndimage.label(cand_f, structure=np.ones((3, 3)))
strong_f = ndimage.maximum(cresp, lab_f, range(1, nf + 1))
keep_f = np.zeros(nf + 1, bool)
keep_f[1:] = np.asarray(strong_f) > FZ_HI
ridge = ridge | (keep_f[lab_f] & cand_f)
print("ridge px", int(ridge.sum()))

NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def longest_paths(mask, min_len):
    """Ordered (x, y) polylines: in each 8-connected piece the longest path, then the longest of what is left, while at least min_len px."""
    out = []
    todo = [c for c in components(mask)]
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
        used = set(path)
        # drop the path and its 1 px halo, then what is left in pieces
        halo = set()
        for y, x in path:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    halo.add((y + dy, x + dx))
        rest = [p for p in px if p not in halo]
        if rest:
            sub = np.zeros_like(mask)
            for y, x in rest:
                sub[y, x] = True
            todo.extend(components(sub))
    return out


def components(mask):
    lab_, k = ndimage.label(mask, structure=np.ones((3, 3)))
    if k == 0:
        return []
    objs = ndimage.find_objects(lab_)
    res = []
    for i, sl in enumerate(objs, 1):
        ys, xs = np.nonzero(lab_[sl] == i)
        res.append([(int(y + sl[0].start), int(x + sl[1].start)) for y, x in zip(ys, xs)])
    return res


paths = longest_paths(ridge, MIN_LEN)
print("paths", len(paths), "total px", sum(len(p) for p in paths))


def smooth(path):
    a = np.array(path, float)
    if len(a) > 8:
        a = np.stack([ndimage.gaussian_filter1d(a[:, j], SMOOTH, mode="nearest") for j in (0, 1)], 1)
    return a


lines = [smooth(p) for p in paths]
if len(sys.argv) > 1 and sys.argv[1] == "view":
    x0, y0, x1, y1 = map(int, sys.argv[2:6])
    z = int(sys.argv[6]) if len(sys.argv) > 6 else 3
    import os

    src = "out/risa_adult/contrast.png" if os.environ.get("VIEW") == "contrast" else "ref/risa-adult/00-bikini.png"
    base = Image.open(src).convert("RGB").crop((x0, y0, x1, y1)).resize(((x1 - x0) * z, (y1 - y0) * z), Image.LANCZOS)
    plain = base.copy()
    d = ImageDraw.Draw(base)
    for ln in lines:
        d.line([((x - x0) * z, (y - y0) * z) for x, y in ln], fill=(255, 40, 40) if os.environ.get("VIEW") == "contrast" else (0, 255, 255), width=2 if os.environ.get("VIEW") == "contrast" else 1)
    sheet = Image.new("RGB", (base.width * 2 + 16, base.height), "white")
    sheet.paste(plain, (0, 0))
    sheet.paste(base, (base.width + 16, 0))
    sheet.save("out/risa_adult/strands-view.png")
    print("wrote out/risa_adult/strands-view.png", sheet.size)
else:
    # a line that runs down to the face's edge ends on it (the skin is drawn over what passes it): found by the distance of an end to the face mask's boundary, the
    # line turned so that end is last. Those go in `edge`, drawn with a blunt end; the rest taper out inside the hair.
    face = m["face"]
    dist = ndimage.distance_transform_edt(~face)
    chains, edge = [], []
    for ln in lines:
        a_end, z_end = ln[0], ln[-1]
        da, dz = dist[int(round(a_end[1])), int(round(a_end[0]))], dist[int(round(z_end[1])), int(round(z_end[0]))]
        near = min(da, dz) < 7
        if near and da < dz:
            ln = ln[::-1]
        pts = [((x - OX) / S, (y - OY) / S) for x, y in ln[::2]]
        if len(pts) < 4:
            continue
        (edge if near else chains).append(tl.fit_chain(pts, tl.simplify(pts, SIMPLIFY)))
    json.dump({"inside": chains, "edge": edge}, open("out/risa_adult/strands.json", "w"), default=lambda o: list(o))
    print("wrote out/risa_adult/strands.json,", len(chains), "inside chains and", len(edge), "edge chains")
