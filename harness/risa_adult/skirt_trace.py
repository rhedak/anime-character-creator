"""Risa's pleated skirt, traced from the full-skirt reference (ref/risa-adult/07-skirt-bikini.png and its `blue-pleated-skirt` layer).

    PYTHONPATH=.claude/skills/trace-reference ./harness/run.sh harness/risa_adult/skirt_trace.py [view]

The first trace was off the clothed uniform (01), where the blazer hides the skirt's top and the sleeves its sides, so what it got was a band, and the shirt over it was too small. 07 shows
the whole skirt over the bikini top: waistband, every pleat, the hem all the way round. Everything is read in the bikini's grid (harness/risa_adult/registration.py, by the irises) and then
mapped onto our body landmark to landmark (`to_body`: the torso is lower and the hips wider on ours than on Risa's), x in head heights from the centre line, d below the chin.

  silhouette   the layer itself (its top is the waistband's curve, its hem the slanted lower edge where the panels step), eroded 2 px so the line sits on the centre of our stroke
  folds        the dark thin lines between the panels, valleys of the luminance walked into polylines (the ridge method of strands_auto.py)
  band         the waistband's lower edge, one line: the silhouette's own top edge shifted down by the band's depth (35 px, measured), so it has no gaps

Writes out/risa_adult/skirt.json and ts/src/body-adult-skirt-pleated-data.ts. `view` writes out/risa_adult/skirt-view.png instead.
"""

import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import ConvexHull

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

C, CHIN, H = 668.2, 434.0, 352.0
sys.path.insert(0, "harness/risa_adult")
from registration import Registration, to_body  # noqa: E402

# everything is read in the bikini's grid (harness/risa_adult/registration.py)
REG = Registration("ref/risa-adult/07-skirt-bikini.png")
img = np.array(REG.register(Image.open("ref/risa-adult/07-skirt-bikini.png").convert("RGB"))).astype(float)
lum = img.mean(2)
layer = np.array(REG.register(Image.open("ref/risa-adult/segments/07-skirt-bikini/blue-pleated-skirt.png").convert("RGBA"), Image.BILINEAR))[..., 3] > 200
Hh, Ww = lum.shape


def hull(mask):
    ys, xs = np.nonzero(mask)
    pts = np.stack([xs, ys], 1)
    hv = ConvexHull(pts).vertices
    out = Image.new("L", (mask.shape[1], mask.shape[0]), 0)
    ImageDraw.Draw(out).polygon([tuple(map(float, pts[i])) for i in hv], fill=255)
    return np.array(out) > 0


silh = ndimage.binary_opening(ndimage.binary_closing(layer, iterations=2), structure=np.ones((3, 3)))
silh = ndimage.binary_erosion(silh, iterations=2)
inner = ndimage.binary_erosion(layer, iterations=2)


def to_r(pts):
    return [to_body(x, y) for x, y in pts]


# ---- fold lines: valleys of the luminance inside the layer
SIG = 1.2
MIN_PATH = 14
Lxx, Lyy, Lxy = (ndimage.gaussian_filter(lum, SIG, order=o) for o in ((0, 2), (2, 0), (1, 1)))
tr, det = Lxx + Lyy, Lxx * Lyy - Lxy**2
lam = tr / 2 + np.sqrt(np.maximum(tr**2 / 4 - det, 0))
nx, ny = Lxy, lam - Lxx
nn = np.maximum(np.hypot(nx, ny), 1e-9)
nx, ny = nx / nn, ny / nn
resp = lam * SIG**2
yy, xx = np.mgrid[0:Hh, 0:Ww].astype(float)
nms = (resp >= ndimage.map_coordinates(resp, [yy + ny, xx + nx], order=1)) & (resp >= ndimage.map_coordinates(resp, [yy - ny, xx - nx], order=1))
cand = nms & (resp > 5.0) & inner & (lum < 75)
lab, n = ndimage.label(cand, structure=np.ones((3, 3)))
mx = ndimage.maximum(resp, lab, range(1, n + 1))
keep = np.zeros(n + 1, bool)
keep[1:] = np.asarray(mx) > 12.0
ridge = keep[lab] & cand

NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def longest_paths(mask, min_len):
    out = []
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
            l2, k2 = ndimage.label(sub, structure=np.ones((3, 3)))
            todo.extend([[(int(y), int(x)) for y, x in zip(*np.nonzero(l2 == i))] for i in range(1, k2 + 1)])
    return out


paths = [p if p[0][1] < p[-1][1] else p[::-1] for p in longest_paths(ridge, MIN_PATH)]  # top to bottom


def smooth(path, sig=2.0):
    a = np.array(path, float)
    return np.stack([ndimage.gaussian_filter1d(a[:, j], sig, mode="nearest") for j in (0, 1)], 1)


def upright(p):
    a = np.array(p, float)
    return np.ptp(a[:, 1]) >= 1.5 * np.ptp(a[:, 0])  # the pieces of the band's line (the detector broke it in places) are not folds: the band is drawn whole, below


lines = [smooth(p) for p in paths if upright(p)]

# ---- the waistband's lower edge, whole: the skirt's own top edge shifted down by the band's depth. Measured on the reference by `$TMPDIR/band.py`-style columns: the dark line sits 35 px
# (0.099 H) under the layer's top edge in every column from 540 to 800 but where a fold line crosses it (33 to 35 px), so it follows the top edge exactly. From the left side of the skirt
# to the right, at that depth.
BAND_DROP = 35
cols = np.arange(Ww)
top_row = np.array([np.nonzero(layer[:, x])[0].min() if layer[:, x].any() else -1 for x in cols], float)
have = top_row >= 0
# only the columns where the top edge is the waistband's own (it sags 23 px from the corners to the middle); past the corners the top row is the slanted side
centre = int(np.round(np.mean(np.nonzero(layer.any(0))[0])))
ok = have & (top_row <= top_row[have].min() + 30)
lo = hi = centre
while lo - 1 >= 0 and ok[lo - 1]:
    lo -= 1
while hi + 1 < Ww and ok[hi + 1]:
    hi += 1
xl, xr = lo + 14, hi - 14  # the corners themselves hook down into the slanted sides
xs = np.arange(xl, xr + 1)
tops = ndimage.gaussian_filter1d(top_row[xs], 5.0, mode="nearest")
band_line = np.stack([xs, tops + BAND_DROP], 1)


def extend(line, end):
    """The band's end carried on along its own slope (a line through its last 30 px) until it meets the skirt's outline (`silh`, the layer eroded 2 px), one pixel at a time."""
    seg = line[:30] if end == "left" else line[-30:]
    slope = np.polyfit(seg[:, 0], seg[:, 1], 1)[0]
    x, y = (line[0] if end == "left" else line[-1]).tolist()
    step = -1.0 if end == "left" else 1.0
    pts = []
    for _ in range(80):
        x += step
        y += slope * step
        if not silh[int(round(y)), int(round(x))]:
            break
        pts.append((x, y))
    return np.array(pts) if pts else np.zeros((0, 2))


left = extend(band_line, "left")
right = extend(band_line, "right")
band_line = np.vstack([left[::-1], band_line, right]) if len(left) or len(right) else band_line

# ---- shades: the darker strips beside the folds
shade_mask = layer & (lum >= 58) & (lum < 108)
shade_mask = ndimage.binary_opening(shade_mask, structure=np.ones((3, 3)))
lab_s, ns = ndimage.label(shade_mask, structure=np.ones((3, 3)))
def thin_and_tall(c):
    ys_, xs_ = np.nonzero(c)
    return c.sum() >= 80 and ys_.max() - ys_.min() >= 40 and xs_.max() - xs_.min() <= 16


shades = [lab_s == i for i in range(1, ns + 1) if thin_and_tall(lab_s == i)]

if len(sys.argv) > 1 and sys.argv[1] == "view":
    z = 3
    box = (430, 930, 920, 1280)
    base = Image.fromarray(img.astype(np.uint8)).crop(box).resize(((box[2] - box[0]) * z, (box[3] - box[1]) * z), Image.LANCZOS)
    d = ImageDraw.Draw(base)
    sm = silh & ~ndimage.binary_erosion(silh)
    for y, x in zip(*np.nonzero(sm[box[1] : box[3], box[0] : box[2]])):
        d.rectangle([x * z, y * z, x * z + 1, y * z + 1], fill=(255, 255, 0))
    for s in shades:
        e = s & ~ndimage.binary_erosion(s)
        for y, x in zip(*np.nonzero(e[box[1] : box[3], box[0] : box[2]])):
            d.rectangle([x * z, y * z, x * z + 1, y * z + 1], fill=(0, 255, 120))
    for ln in lines:
        d.line([((x - box[0]) * z, (y - box[1]) * z) for x, y in ln], fill=(255, 40, 40), width=2)
    d.line([((x - box[0]) * z, (y - box[1]) * z) for x, y in band_line], fill=(255, 0, 255), width=2)
    base.save("out/risa_adult/skirt-view.png")
    print("fold lines", len(lines), "shades", len(shades), "silhouette px", int(silh.sum()), "wrote out/risa_adult/skirt-view.png", base.size)
    sys.exit(0)

sil_chain = tl.fit_closed(to_r(tl.boundary(silh)), 0.004)
fold_chains = []
for ln in lines:
    pts = to_r([tuple(v) for v in ln[::2]])
    if len(pts) >= 3:
        fold_chains.append(tl.fit_chain(pts, tl.simplify(pts, 0.003)))
band_pts = to_r([tuple(v) for v in band_line[::4]] + [tuple(band_line[-1])])
band_chain = tl.fit_chain(band_pts, tl.simplify(band_pts, 0.002))
json.dump({"silhouette": sil_chain, "folds": fold_chains, "band": band_chain}, open("out/risa_adult/skirt.json", "w"), default=lambda o: list(o))


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


def chain(c):
    st, sg = c
    return f"[{pt(st)}, [{', '.join(f'[{pt(cc)}, {pt(e)}]' for cc, e in sg)}]]"


def arr(name, doc, cs):
    body = ",\n  ".join(chain(c) for c in cs)
    return f"/** {doc} */\nexport const {name}: readonly Chain[] = [\n  {body},\n];\n"


Path("ts/src/body-adult-skirt-pleated-data.ts").write_text(
    "// Generated by harness/risa_adult/skirt_trace.py from the pleated skirt of ref/risa-adult/01-school-uniform.png. Do not edit by hand.\n"
    "// Points are [x, d]: x in head heights from the body's centre line, d in head heights below the chin.\n\n"
    'import type { Chain } from "./tables.ts";\n\n'
    + f"/** The skirt's silhouette: the flare with its slanted hem, the top hidden under the blazer. */\nexport const ADULT_PLEATED_SKIRT: Chain = {chain(sil_chain)};\n\n"
    + arr("ADULT_PLEATED_FOLDS", "The dark fold lines between the panels, each from the waistband's lower edge to the hem.", fold_chains)
    + f"\n/** The waistband's lower edge, one line across the skirt: its top edge shifted down by the band's depth. */\nexport const ADULT_PLEATED_BAND: Chain = {chain(band_chain)};\n"
)
print("silhouette", len(sil_chain[1]), "segments;", len(fold_chains), "folds; wrote ts/src/body-adult-skirt-pleated-data.ts")
