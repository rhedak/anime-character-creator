"""Trace Kou off his own reference, in units of his wingspan.

    ./harness/run.sh harness/kou/trace_kou.py

`../time_slider_katherina/style-anchors/kou_grok/kou.png` was generated to be
traced (`scratchpad/kou/kou_reference_prompt.txt`): flat single-tone surfaces,
pure-black outlines, a light background, nothing overlapping him. So the regions
are the reference's own fills, the same method the hat's crown/band/bow and the
jacket's panels came from, with no hidden stretch to infer anywhere:

  body    head, ears and feet in one fill
  wings   each wing is split into cells by its finger struts; the cells unioned
          are the wing, and drawn as cells they give the struts back for free
  eyes    the two black discs, holes in the body's fill
  lines   the ink inside the body: the ear ridges, the nose and the mouth

Coordinates are in wingspan units (1.0 = tip to tip), origin at the centre of
his bounding box, so placing him is two numbers in `character.py`: how wide he
is in head radii, and where his centre sits. Nothing here knows about Katherina.

Writes `out/kou/kou.json` and `out/kou/kou_overlay.png`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".claude/skills/trace-reference"))
import trace_lib as tl  # noqa: E402

REF = Path(__file__).resolve().parents[3] / "time_slider_katherina/style-anchors/kou_grok/kou.png"
OUT = Path("out/kou")
HALF_STROKE = 4  # the reference's outline is about 8 px

rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
s = rgb.sum(2)
disk = ndi.generate_binary_structure(2, 1)

creature = ndi.binary_fill_holes(s < 400)
ys, xs = np.nonzero(creature)
X0, X1, Y0, Y1 = xs.min(), xs.max(), ys.min(), ys.max()
SPAN = X1 - X0
CX, CY = (X0 + X1) / 2, (Y0 + Y1) / 2
print("bbox", X0, X1, Y0, Y1, "span", SPAN, "centre", CX, CY)


def hr(pts):
    return [((x - CX) / SPAN, (y - CY) / SPAN) for x, y in pts]


def grow(m, n):
    return ndi.binary_dilation(m, structure=disk, iterations=n) if n else m


def close(m, n):
    return ndi.binary_fill_holes(ndi.binary_erosion(grow(m, n), structure=disk, iterations=n))


def trace(m, tol, smooth=0.0):
    if smooth:
        m = ndi.gaussian_filter(m.astype(float), smooth) > 0.5
    start, segs = tl.fit_closed(hr(tl.boundary(m)), tol)
    return {"start": start, "segs": segs}


fill = (s > 20) & (s < 400)
lab, n = ndi.label(fill)
sizes = ndi.sum(fill, lab, range(1, n + 1))
order = np.argsort(sizes)[::-1] + 1
body_id = int(order[0])
body = lab == body_id

# Each wing: the cells on that side, unioned and closed across their struts.
wing_cells = {"left": [], "right": []}
for i in order[1:]:
    m = lab == i
    if m.sum() < 3000:
        continue
    cxs = np.nonzero(m)[1]
    wing_cells["left" if cxs.mean() < CX else "right"].append(m)
print("wing cells:", {k: len(v) for k, v in wing_cells.items()})

result = {"span_px": int(SPAN)}
over = Image.open(REF).convert("RGB")
d = ImageDraw.Draw(over)

result["body"] = trace(grow(close(body, 6), HALF_STROKE), 0.004, smooth=2)
d.line([(CX + x * SPAN, CY + y * SPAN) for x, y in tl.sample_chain(result["body"]["start"], result["body"]["segs"], 8)], fill="#00ff66", width=3)
print("body segments", len(result["body"]["segs"]))

for side, cells in wing_cells.items():
    whole = np.zeros(s.shape, bool)
    for m in cells:
        whole |= m
    result[f"wing_{side}"] = trace(grow(close(whole, 10), HALF_STROKE), 0.004, smooth=2)
    c = result[f"wing_{side}"]
    d.line([(CX + x * SPAN, CY + y * SPAN) for x, y in tl.sample_chain(c["start"], c["segs"], 8)], fill="#33aaff", width=3)
    result[f"wing_{side}_cells"] = []
    for m in sorted(cells, key=lambda m: np.nonzero(m)[1].mean()):
        cell = trace(grow(close(m, 4), HALF_STROKE), 0.004, smooth=2)
        result[f"wing_{side}_cells"].append(cell)
        d.line([(CX + x * SPAN, CY + y * SPAN) for x, y in tl.sample_chain(cell["start"], cell["segs"], 8)], fill="#ffee00", width=1)
    print(side, "wing segments", len(c["segs"]), "cells", [len(k["segs"]) for k in result[f"wing_{side}_cells"]])

# The eyes: black discs enclosed by the body's fill.
black = s < 20
holes = ndi.binary_fill_holes(body) & ~body & black
hl, hn = ndi.label(holes)
eyes = []
for i in range(1, hn + 1):
    m = hl == i
    if m.sum() < 2000:
        continue
    eyes.append(m)
eyes.sort(key=lambda m: np.nonzero(m)[1].mean())
result["eyes"] = []
for m in eyes:
    c = trace(grow(m, 1), 0.003, smooth=2)
    result["eyes"].append(c)
    d.line([(CX + x * SPAN, CY + y * SPAN) for x, y in tl.sample_chain(c["start"], c["segs"], 8)], fill="#ff2255", width=2)
print("eyes", len(result["eyes"]), [int(m.sum()) for m in eyes])

# Ink inside the body that is not its outline: the ear ridges, nose and mouth.
inner = ndi.binary_erosion(close(body, 6), disk, HALF_STROKE + 3)
ink = inner & black & ~ndi.binary_dilation(np.logical_or.reduce(eyes), disk, 3)
il, iN = ndi.label(ink, structure=np.ones((3, 3)))
result["lines"] = []
for i in range(1, iN + 1):
    m = il == i
    if m.sum() < 150:
        continue
    pts = np.column_stack(np.nonzero(m)[::-1]).astype(float)
    mu = pts.mean(0)
    u = np.linalg.svd(pts - mu, full_matrices=False)[2][0]
    t = (pts - mu) @ u
    o = np.argsort(t)
    bins = np.array_split(o, 8)
    cl = [pts[o[0]], *[pts[b].mean(0) for b in bins if len(b)], pts[o[-1]]]
    h = hr(cl)
    st, sg = tl.fit_chain(h, tl.simplify(h, 0.004))
    result["lines"].append({"start": st, "segs": sg, "px": int(m.sum())})
    d.line([(CX + x * SPAN, CY + y * SPAN) for x, y in tl.sample_chain(st, sg, 8)], fill="#ff8800", width=3)
print("interior lines", [ln["px"] for ln in result["lines"]])

result["colors"] = {
    "fur": "#%02x%02x%02x" % tuple(np.median(rgb[ndi.binary_erosion(body, iterations=4)], axis=0).astype(int)),
    "membrane": "#%02x%02x%02x" % tuple(np.median(rgb[ndi.binary_erosion(wing_cells["left"][0], iterations=4)], axis=0).astype(int)),
}
print(result["colors"])
OUT.mkdir(parents=True, exist_ok=True)
json.dump(result, open(OUT / "kou.json", "w"), indent=1, default=float)
over.crop((X0 - 30, Y0 - 30, X1 + 30, Y1 + 30)).save(OUT / "kou_overlay.png")
