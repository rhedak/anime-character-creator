"""Trace the blouse of ref 02 (the segment layer white-blouse.png) into ts/src/body-adult-blouse-data.ts.

    PYTHONPATH=.claude/skills/trace-reference ./harness/run.sh harness/franzi/blouse_trace.py

Same method as bottom_trace.py. The blouse is one silhouette: bodice and both puff sleeves, the sweetheart neckline with its scalloped edge, the frilled
cuffs and the hem with the opening at the front. Coordinates are the body's own: depth d in head heights below the chin (row 434 of the reference canvas is
d = 0, a head height is 352 px) and x in head heights from the garment's own centre line (the opening at the hem and the point of the neckline are on
column C, found from them), so `place()` in body-adult-parts.ts maps them onto the skeleton as it does the top and the briefs. The mask is eroded 3 px so the
line sits on the centre of our stroke. The figure leans a few px in the reference and the frills are not alike on the two sides, so the blouse is made
symmetric by tracing the viewer's left half and mirroring it (averaging the halves doubled every scallop).

The inside lines are the ones the reference draws and a flat garment keeps: the binding along the neckline (the neckline's edge offset inwards), the seam
where each sleeve joins the bodice, the gather above each cuff's frill, and the front opening's line. The first is computed from the mask; the others are read
off the reference at 2x (out/franzi/blouse-grid.png) as a few points each and given as a left-hand polyline [v, d] (v the distance from the centre line, the
right hand is the mirror). Writes out/franzi/blouse.json and ts/src/body-adult-blouse-data.ts.
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/franzi")
CHIN, H = 434.0, 352.0
mask0 = np.array(Image.open("ref/franzi/segments/02-blouse/white-blouse.png"))[..., 3] > 128
# the garment's centre line: the point of the neckline and the opening at the hem
rows_hem = [y for y in range(1070, 1125) if (~mask0[y, 600:720]).any() and mask0[y, 600:720].any()]
slit_cols = [np.nonzero(~mask0[y, 630:690])[0].mean() + 630 for y in rows_hem if (~mask0[y, 630:690]).any() and mask0[y, 630:640].any() and mask0[y, 680:690].any()]
V_ROW = next(y for y in range(640, 760) if mask0[y, 640:680].all())  # first row where the middle is cloth: below the neckline's point
v_cols = [np.nonzero(~mask0[V_ROW - 3, 600:720])[0].mean() + 600]
C_slit = float(np.mean(slit_cols)) if slit_cols else None
print("slit centre", C_slit, "V point row", V_ROW, "neckline point column", v_cols[0])
C = float(np.mean([c for c in [C_slit, v_cols[0]] if c is not None]))
print("garment centre column %.2f" % C)

# Where a puff meets its frill, and where the cuff's hem meets the bodice at the armpit, the reference leaves a narrow wedge of page. Drawn as two strokes it is
# narrower than the strokes are wide and fills in solid black (the owner: the outline between the sleeve and the puff looked cut off and odd), so in the sleeve
# zone the wedges are closed. Elsewhere (the neckline, the opening at the hem) the slits are left as they are.
CLOSE_R = 9
disc = np.hypot(*np.mgrid[-CLOSE_R : CLOSE_R + 1, -CLOSE_R : CLOSE_R + 1]) <= CLOSE_R
closed = ndimage.binary_closing(np.pad(mask0, CLOSE_R + 2), structure=disc)[CLOSE_R + 2 : -(CLOSE_R + 2), CLOSE_R + 2 : -(CLOSE_R + 2)]
xs_all = np.arange(mask0.shape[1])[None, :]
zone = (np.arange(mask0.shape[0])[:, None] > 730) & (np.arange(mask0.shape[0])[:, None] < 850) & (np.abs(xs_all - C) > 100)
mask0 = np.where(zone, closed, mask0)
mask = ndimage.binary_erosion(mask0, iterations=3)
Ci = int(round(C))
left = mask.copy()
left[:, Ci:] = False
src = np.clip(np.round(2 * C - np.arange(mask.shape[1])).astype(int), 0, mask.shape[1] - 1)
sym = left | left[:, src]
# a one-pixel crack at the armpit corner, where the hem's end and the torso's side meet, made the outline hook there: closed
armpit = (np.arange(sym.shape[0])[:, None] > 800) & (np.arange(sym.shape[0])[:, None] < 832) & (np.abs(np.arange(sym.shape[1])[None, :] - C) > 110) & (np.abs(np.arange(sym.shape[1])[None, :] - C) < 175)
disc4 = np.hypot(*np.mgrid[-4:5, -4:5]) <= 4
sym = np.where(armpit, ndimage.binary_closing(np.pad(sym, 6), structure=disc4)[6:-6, 6:-6], sym)
# and the cuff's hem ends a few px past the torso's side (a lip of 8 px under it, rows 817 to 821), which drew as a nub where the seam arrives: the lip is filled,
# so the hem runs into the torso's side and the side goes on down from it
sym[815:823, 519:530] = True
sym[815:823, int(round(2 * C)) - 529 : int(round(2 * C)) - 518] = True
# The body this blouse goes on is the one of ref 04 and the blouse is traced from ref 02, where the figure stands a little differently: at the waist the traced
# blouse is slimmer than our body and at the shoulder tops narrower, so the body's outline showed beside it. A garment covers what it is worn on, so each row's
# outer edge is widened, outwards only, to the body's own edge (the shoulder's above the sleeves, the torso's side below them) plus MARGIN, which also covers
# the body's stroke. The neckline and the sleeves, wider than the body, are not touched.
MARGIN = 0.005
body = open("ts/src/body-adult-data.ts").read()


def table(name):
    m = re.search(r"export const %s[^=]*=\s*(\[\[.*?\]\]);" % name, body, re.S)
    return np.array(json.loads(m.group(1)))


SH, TS = table("SHOULDER_OUTER"), table("TORSO_SIDE")
widened = 0
for row in range(int(CHIN + 0.3 * H), int(CHIN + 1.95 * H)):
    d = (row - CHIN) / H
    if 0.3 <= d <= 0.9:
        vmin = float(np.interp(d, SH[:, 0], SH[:, 1]))
    elif 1.1 <= d <= 2.2:
        vmin = float(np.interp(d, TS[:, 0], TS[:, 1]))
    else:
        continue
    cols = np.nonzero(sym[row, Ci:])[0]
    if len(cols) == 0:
        continue
    need = int(np.ceil((vmin + MARGIN) * H))
    have = int(cols.max())
    if have < need and need - have <= 0.06 * H:  # a row far narrower than the body is the hem's curve, not a waist that is too slim
        sym[row, Ci + have : Ci + need + 1] = True
        sym[row, max(0, Ci - need - 1) : Ci - have + 1] = True
        widened += 1
print("rows widened to the body's edge:", widened)
sym = ndimage.gaussian_filter(sym.astype(float), 1.3) > 0.45
np.save(OUT / "blouse_mask.npy", sym)
pts = [((x - C) / H, (y - CHIN) / H) for x, y in tl.boundary(sym)]
start, segs = tl.fit_closed(pts, 0.0035)
xs_ = [p[0] for p in pts]
ds_ = [p[1] for p in pts]
print("blouse extent x", round(min(xs_), 3), round(max(xs_), 3), "d", round(min(ds_), 3), round(max(ds_), 3), "segments", len(segs))

# --- the binding along the neckline: the neckline's edge, 12 px inwards. The neckline is the part of the boundary between the two shoulder tops that is
# not the outside of the garment: rows above V_ROW, columns between the straps' outer edges and the middle.
dist = ndimage.gaussian_filter(ndimage.distance_transform_edt(sym), 2.0)
gy, gx = np.gradient(dist)
bpts = np.array(tl.boundary(sym), float)  # (x, y) px along the boundary


def neckline_run():
    global bpts
    cond = (bpts[:, 1] < V_ROW + 3) & (bpts[:, 0] > 540) & (bpts[:, 0] < 2 * C - 540) & (bpts[:, 1] > 470)
    first_false = int(np.argmin(cond))  # start the loop at a point outside the run, so the run does not wrap round the list's end
    bpts = np.roll(bpts, -first_false, axis=0)
    cond = np.roll(cond, -first_false)
    idx = np.nonzero(cond)[0]
    runs, cur = [], [idx[0]]
    for i in idx[1:]:
        if i == cur[-1] + 1:
            cur.append(i)
        else:
            runs.append(cur)
            cur = [i]
    runs.append(cur)
    return bpts[max(runs, key=len)]


run = neckline_run()
if run[0, 0] > run[-1, 0]:
    run = run[::-1]  # left to right: for the right half, the point first and the strap's top last
run = np.stack([ndimage.gaussian_filter1d(run[:, 0], 4.0, mode="nearest"), ndimage.gaussian_filter1d(run[:, 1], 4.0, mode="nearest")], 1)
BIND = 12.0
inner = []
for x, y in run:
    nx, ny = gx[int(y), int(x)], gy[int(y), int(x)]
    n = np.hypot(nx, ny) or 1.0
    inner.append((x + BIND * nx / n, y + BIND * ny / n))
inner = np.array(inner)
print("run", run[0], run[-1], len(run), "inner x range", np.nanmin(inner[:,0]), np.nanmax(inner[:,0]))
# one half, from the strap's top to the centre line, sampled every ~14 px
inner = inner[inner[:, 0] >= C - 0.5][::-1]  # the mask is symmetric, so the right half serves for the left: from the strap's top down to the point
sel = np.linspace(0, len(inner) - 1, max(8, int(len(inner) / 14))).astype(int)
binding = [((x - C) / H, (y - CHIN) / H) for x, y in inner[sel]]
binding[-1] = (0.0, binding[-1][1])  # ends on the centre line at the point of the neckline
binding = binding[3:]  # the first samples sit on the strap's top edge, where the inward normal points along the edge and the line hooked out in two short ticks
print("binding: %d points, from d %.3f to %.3f, run of %d boundary px" % (len(binding), binding[0][1], binding[-1][1], len(run)))

# --- the lines read off the reference at 2x, left hand, canvas px (x, y): the sleeve seam, the gather above the cuff's frill, the front opening
# Both run past the cloth's outline at each end (the draw clips them to it), so each ends on the outline and not a few px short of it: the seam from above the shoulder
# to below the cuff's hem, the gather from outside the sleeve's outer edge to the seam.
# The sleeve seam is the side of the bodice, which at the bust is the side of the breast: in the reference it is the dark line that runs straight down the shoulder
# panel (v 0.43 H), bulges out round the bust to 0.46 H at 0.78 H below the chin and comes in to 0.38 H at the cuff's hem. Read off the reference by the darkest pixel of
# each row (rows 540 to 800, viewer's left, smoothed; the right hand is the mirror: the figure leans in ref 02 and the right side reads 0.04 wider), as [v, d]. The
# first version took five points by eye and drew it nearly straight (0.444 to 0.450 to 0.442), so the breast's outer side read as a straight line (the owner). It
# ends at the corner where the cuff's hem meets the torso's side (v 0.389 H, 1.096 H below the chin, row 820 of the reference), so the seam goes on as the torso's
# outline without a break; it used to run on past the corner (to 1.12 H, 0.352 H) and showed as a tick inside the torso. It
# stays outside the full breast contour (ADULT_BREAST, body-adult-bust-data.ts) by at least MARGIN_BUST, checked in the harness's red-contour view.
SEAM_VD = [(0.424, 0.14), (0.428, 0.24), (0.431, 0.36), (0.432, 0.50), (0.437, 0.61), (0.447, 0.68), (0.458, 0.74), (0.462, 0.80), (0.454, 0.87), (0.432, 0.93), (0.410, 0.99), (0.395, 1.05), (0.389, 1.096)]
GATHER = [(400, 786), (428, 778), (452, 770), (478, 774), (503, 780), (507, 783)]
OPENING = [(C, V_ROW + 4), (C, 1110)]


def to_body(line):
    return [((C - x) / H, (y - CHIN) / H) for x, y in line]


lines = {"seam": SEAM_VD, "gather": to_body(GATHER), "binding": binding}
opening_d = [(OPENING[0][1] - CHIN) / H, (OPENING[1][1] - CHIN) / H]
json.dump({"blouse": (start, segs), "centre": C, "lines": lines, "opening": opening_d}, open(OUT / "blouse.json", "w"), default=lambda o: list(o))


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


def poly(name, ps):
    return f"  {name}: [{', '.join(pt(p) for p in ps)}],\n"


body = ", ".join(f"[{pt(c)}, {pt(e)}]" for c, e in segs)
Path("ts/src/body-adult-blouse-data.ts").write_text(
    "// Generated by harness/franzi/blouse_trace.py from the blouse layer of ref 02. Do not edit by hand.\n"
    "// Points are [x, d]: x in head heights from the garment's centre line, d in head heights below the chin; the outline is symmetric.\n"
    "// The lines are the viewer's left hand, [v, d] with v the distance from the centre line; the right hand is the mirror image.\n\n"
    'import type { Chain } from "./tables.ts";\n\n'
    f"export const ADULT_BLOUSE: Chain = [{pt(start)}, [{body}]];\n\n"
    "export const ADULT_BLOUSE_LINES = {\n"
    + poly("seam", lines["seam"])
    + poly("gather", lines["gather"])
    + poly("binding", lines["binding"])
    + f"  opening: [{opening_d[0]:.4f}, {opening_d[1]:.4f}],\n"
    "} as const;\n"
)
print("wrote ts/src/body-adult-blouse-data.ts")
