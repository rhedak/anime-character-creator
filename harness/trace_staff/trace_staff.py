"""Trace the staff off the full reference, in head radii (same calibration as the hat).

Shapes, in drawing order:
  wood       whole wooden silhouette (prongs, knot, braid, shaft), the shaft bridged
             across where the reference's fist hides it
  strands    the braid's and prongs' separate strands: components of the wood's fill
             split by its darker structural lines (threshold 90 keeps grain inside)
  crystal    the gem's outline
  facets     its dark and light faces, from three smoothed brightness bands
Landmarks: the grip (shaft centre line at the reference fist's centre) and the tip.
"""

import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, "/Users/henrik/git/anime-character-creator/.claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

REF = "/Users/henrik/git/time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OUT = "out/trace_staff"
OX, OY, SCALE = 650.0, 481.0, 173.7
HALF_STROKE = 3

rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
s = rgb.sum(2)
r = rgb[..., 0]
disk = ndi.generate_binary_structure(2, 1)
ROWS = np.arange(s.shape[0])[:, None]


def grow(m, n):
    return ndi.binary_dilation(m, structure=disk, iterations=n) if n else m


def close(m, n):
    return ndi.binary_fill_holes(ndi.binary_erosion(grow(m, n), structure=disk, iterations=n))


def largest(m):
    lab, n = ndi.label(m)
    if n <= 1:
        return m
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    return lab == int(np.argmax(sizes))


def hexc(px):
    return "#%02x%02x%02x" % tuple(int(v) for v in np.median(px, axis=0))


def wood_components(thr, min_px):
    lab, _ = ndi.label(s > thr)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        if sl is None:
            continue
        ys, xs = sl
        if xs.start < 140 or xs.stop > 470 or ys.start < 290 or ys.stop > 1530:
            continue
        m = lab[sl] == i
        if m.sum() < min_px:
            continue
        rr, gg, bb = np.median(rgb[sl][m], axis=0)
        if 40 < rr < 160 and rr > gg > bb and rr - bb > 15:
            full = np.zeros(s.shape, bool)
            full[sl] = m
            out.append(full)
    return out


# --- crystal (cut at its own colour so the knot's glow does not leak in)
lab60, _ = ndi.label(s > 60)
crystal = largest(ndi.binary_fill_holes(ndi.binary_opening((lab60 == lab60[520, 275]) & (r > 170), iterations=2)))

# --- wood
wood = np.zeros(s.shape, bool)
for m in wood_components(60, 30):
    wood |= m
wood &= ~grow(crystal, 1)

FIST_TOP, FIST_BOT = 884, 984
wood_c = close(wood, 3)


def edges(y):
    xs = np.nonzero(wood_c[y])[0]
    return np.array([xs.min(), xs.max()], float)


a0 = np.mean([edges(y) for y in range(FIST_TOP - 12, FIST_TOP)], axis=0)
b0 = np.mean([edges(y) for y in range(FIST_BOT, FIST_BOT + 12)], axis=0)
bridge = np.zeros(s.shape, bool)
y0, y1 = FIST_TOP - 6, FIST_BOT + 6
for y in range(y0, y1):
    t = (y - y0) / (y1 - y0)
    lo, hi = (1 - t) * a0 + t * b0
    bridge[y, round(lo) : round(hi) + 1] = True
wood_all = largest(close(wood | bridge, 4))
# Below the fist the shaft gets shortened to reach this figure's ground (about
# 0.4 of its length at chibi), which bunches its small knots into spikes. Smooth
# that stretch of the mask first, so only the reference's gentle waviness and its
# taper survive the compression.
LOW_SIGMA = 7.0
soft = ndi.gaussian_filter(wood_all.astype(float), LOW_SIGMA) > 0.5
# Above it, only a light pass: the reference's hand-drawn edge wobbles by a pixel
# or two between knots, which fits into zigzags at this generator's line weight.
light_soft = ndi.gaussian_filter(wood_all.astype(float), 2.5) > 0.5
wood_all = largest(np.where(ROWS > FIST_TOP, soft, light_soft | (wood_all & ~grow(light_soft, 2))))

# --- strands: structural pieces of the upper wood
strands = [
    m for m in wood_components(90, 800) if np.nonzero(m)[0].min() < 880 and m.sum() < 0.6 * wood.sum()
]
print("strands", len(strands), [int(m.sum()) for m in strands])

# --- crystal tone bands
sm = ndi.median_filter(s, size=7)
dark = ndi.binary_opening(crystal & (sm < 440), iterations=2)
light = ndi.binary_opening(crystal & (sm >= 560), iterations=1)

# --- landmarks
fist = (lab60 == lab60[930, 345]) | (lab60 == lab60[950, 330])
fy, fx = np.nonzero(fist)
grip_y = fy.mean()
t = (grip_y - y0) / (y1 - y0)
glo, ghi = (1 - t) * a0 + t * b0
grip = (((glo + ghi) / 2 - OX) / SCALE, (grip_y - OY) / SCALE)
wy, wx = np.nonzero(wood_all)
tip_row = wy.max()
tip = ((wx[wy >= tip_row - 3].mean() - OX) / SCALE, (tip_row - OY) / SCALE)
top_y = (min(wy.min(), np.nonzero(crystal)[0].min()) - OY) / SCALE
print("grip", grip, "tip", tip, "top", top_y)


def hr(pts):
    return [((x - OX) / SCALE, (y - OY) / SCALE) for x, y in pts]


result = {"grip": grip, "tip": tip, "top_y": top_y}
over = Image.fromarray(np.clip(rgb * 2.5, 0, 255).astype("uint8"))
d = ImageDraw.Draw(over)


def trace(m, tol):
    start, segs = tl.fit_closed(hr(tl.boundary(m)), tol)
    return {"start": start, "segs": segs}


def draw(c, col, w=2):
    poly = tl.sample_chain(c["start"], c["segs"], 10)
    d.line([(OX + x * SCALE, OY + y * SCALE) for x, y in poly], fill=col, width=w)


result["wood"] = trace(grow(wood_all, HALF_STROKE), 0.014)
draw(result["wood"], "#00ff66")
result["strands"] = []
for m in strands:
    c = trace(grow(ndi.binary_opening(close(m, 4), iterations=2), 2), 0.016)
    result["strands"].append(c)
    draw(c, "#ff2255", 1)
result["crystal"] = trace(grow(crystal, HALF_STROKE), 0.008)
draw(result["crystal"], "#33aaff")
result["facets_dark"], result["facets_light"] = [], []
for key, mask, min_px, col in (("facets_dark", dark, 300, "#8844ff"), ("facets_light", light, 120, "#ffffff")):
    flab, fn = ndi.label(mask)
    for i in range(1, fn + 1):
        m = flab == i
        if m.sum() < min_px:
            continue
        c = trace(m, 0.006)
        result[key].append(c)
        draw(c, col, 1)
print("segments: wood", len(result["wood"]["segs"]), "crystal", len(result["crystal"]["segs"]),
      "strands", [len(c["segs"]) for c in result["strands"]],
      "dark", [len(c["segs"]) for c in result["facets_dark"]], "light", [len(c["segs"]) for c in result["facets_light"]])

upper = ROWS < 880
result["colors"] = {
    "wood": hexc(rgb[ndi.binary_erosion(wood, iterations=2)]),
    "wood_upper": hexc(rgb[ndi.binary_erosion(wood, iterations=2) & upper]),
    "crystal_mid": hexc(rgb[crystal & ~dark & ~light]),
    "crystal_dark": hexc(rgb[dark]),
    "crystal_light": hexc(rgb[light]),
}
print(result["colors"])
json.dump(result, open(f"{OUT}/staff_trace.json", "w"), indent=1, default=float)
over.crop((140, 290, 500, 1540)).save(f"{OUT}/trace_overlay.png")
over.crop((150, 300, 400, 720)).resize((600, 1008)).save(f"{OUT}/trace_overlay_top.png")
over.crop((230, 620, 420, 1010)).resize((380, 780)).save(f"{OUT}/trace_overlay_mid.png")
