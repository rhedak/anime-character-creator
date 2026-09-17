"""Retrace the jacket body and the sleeve so shoulder and sleeve are one garment.

    ./harness/run.sh harness/clothes/trace_shoulders.py

Supersedes the shoulder half of `trace_jacket.py` and `trace_sleeve.py` (both still
write the lower panels' and the cuff's own traces, which this reuses). The first
pass carried the jacket's outer edge across the hair as a convex hull and stopped
the sleeve flat at the arm's pivot, so without the hair the two read as a vest
beside a tube. What the reference shows where the hair does not cover it:

- the jacket's top edge, a straight shoulder line from the collar's outer corner
  (0.42, 1.11) sloping out at 0.49;
- a seam inside each panel, x about +-0.60, from the shoulder down to the armpit
  (2.03): the sleeve joins the body there, it is not the jacket's side;
- the sleeve's outer edge where it leaves the hair (1.04 at 1.90), sloping 0.28,
  and its centre line.

The shoulder under the hair is inferred from those: the sleeve's top is a disc
about the joint on its centre line whose top touches the shoulder line (joint
(0.729, 1.45), radius 0.19, about half the sleeve's width). A disc is the same at
any angle, so a sleeve swung about that joint still meets the shoulder cleanly.
The jacket's outer edge runs along the shoulder line to the disc, round its upper
inner side to the seam, down the seam, then out to where its side meets the belt.
Each side keeps its own traced front edge and lower panel; the shoulder, cap and
seam geometry is the right side's, mirrored, so the shoulders match. The left arm
wears the same sleeve mirrored.

Writes `out/clothes/shoulders.json` (jacket left/right, sleeve, joint) and
`out/clothes/shoulders_overlay.png`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".claude/skills/trace-reference"))
import trace_lib as tl  # noqa: E402

REF = Path(__file__).resolve().parents[3] / "time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OX, OY, SC = 650.0, 481.0, 173.7
OUT = Path("out/clothes")

rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
r, g = rgb[..., 0], rgb[..., 1]
s = rgb.sum(2)
lab, _ = ndi.label(s > 60)
disk = ndi.generate_binary_structure(2, 1)
H, W = s.shape
YY, XX = np.mgrid[0:H, 0:W]
X = (XX - OX) / SC  # head radii
Y = (YY - OY) / SC

# Measured (see the docstring and the measuring session in the plan doc).
COLLAR_CORNER = (0.42, 1.111)
SHOULDER_SLOPE = 0.49
SEAM = [(0.604, 1.514), (0.614, 1.668), (0.619, 1.802), (0.611, 1.906), (0.593, 2.026)]
SLEEVE_OUT_Y, SLEEVE_OUT_X, SLEEVE_SLOPE = 1.90, 1.042, 0.279
SLEEVE_IN_X_AT_190 = 0.668
BELT_TOP_HR = (878 - OY) / SC

sleeve = ndi.binary_opening((lab == 179) & (r > g + 3), disk, 2)
nl, _ = ndi.label(sleeve)
sz = np.bincount(nl.ravel())
sz[0] = 0
sleeve = nl == np.argmax(sz)


# The hair's strands leave notches in the sleeve's fill where they cross it; each
# edge is instead a straight line fitted where that edge is clear: the inner edge
# from 1.95 to 2.55 (below that the elbow bends it), the outer from 2.20 to 2.90
# (above that the strands cross it), carried up to the joint.
def edge_line(lo, hi, side):
    rows = [y for y in range(round(OY + lo * SC), round(OY + hi * SC)) if sleeve[y].any()]
    ys = np.array([(y - OY) / SC for y in rows])
    xs = np.array([(side(np.nonzero(sleeve[y])[0]) - OX) / SC for y in rows])
    return np.polyfit(ys, xs, 1)


in_line, out_line = edge_line(1.95, 2.55, np.min), edge_line(2.20, 2.90, np.max)
print("sleeve edges: inner", in_line, "outer", out_line)

# The joint: on the sleeve's centre line, at the height where a disc as wide as
# the sleeve there just touches the shoulder line. The cap is then exactly the
# sleeve's width, its edges run into it tangentially, and its top meets the
# shoulder line.
best = None
m = SHOULDER_SLOPE
for jy in np.linspace(1.2, 1.9, 1401):
    jx = (np.polyval(in_line, jy) + np.polyval(out_line, jy)) / 2
    half = (np.polyval(out_line, jy) - np.polyval(in_line, jy)) / 2
    dist = (jy - COLLAR_CORNER[1] - m * (jx - COLLAR_CORNER[0])) / np.hypot(m, 1)
    if best is None or abs(dist - half) < best[0]:
        best = (abs(dist - half), jx, jy, half)
_, JX, JY, RADIUS = best
print("joint", round(JX, 3), round(JY, 3), "radius", round(RADIUS, 3))

seam_ys = np.array([p[1] for p in SEAM])
seam_xs = np.array([p[0] for p in SEAM])


def seam_x(y):
    return np.interp(y, seam_ys, seam_xs, left=seam_xs[0], right=seam_xs[-1])


def hull_mask(m):
    ys, xs = np.nonzero(m)
    h = ConvexHull(np.column_stack([xs, ys]))
    inside = np.ones(m.shape, bool)
    for a, b, c in h.equations:
        inside &= a * XX + b * YY + c <= 0.5
    return inside


def right_side_rule(x, y):
    """The right jacket panel's allowed region above the belt, by geometry."""
    below_shoulder = y >= COLLAR_CORNER[1] + SHOULDER_SLOPE * (x - COLLAR_CORNER[0])
    in_disc = (x - JX) ** 2 + (y - JY) ** 2 < RADIUS**2
    sx = seam_x(y)
    seam_end_y = seam_ys[-1]
    # Below the armpit the side runs out from the seam's foot to the hull at the belt.
    return below_shoulder & (
        (x <= sx) | ((y <= JY) & (x <= JX) & ~in_disc) | (y > seam_end_y)
    )


result = {"joint": (float(JX), float(JY)), "radius": RADIUS}
over = Image.fromarray(np.clip(rgb * 3.0, 0, 255).astype("uint8"))
d = ImageDraw.Draw(over)

# --- each jacket piece: its own traced front edge and lower panel, with the
# shoulder, cap and seam geometry (measured on the right, where the hair leaves
# more of it visible) mirrored onto the left.
for side, sign, upper_id, lower_id in (("right", 1, 179, 202), ("left", -1, 180, 203)):
    SX = sign * X  # the side's own outward x
    navy = (lab == upper_id) & ~(r > g + 3)
    navy = ndi.binary_opening(navy, disk, 2) & (YY < 878)
    nl, _ = ndi.label(navy)
    sz = np.bincount(nl.ravel())
    sz[0] = 0
    navy = nl == np.argmax(sz)
    hull = hull_mask(navy) & (YY < 880)
    # The front edge is the hull's own inner edge, row by row: the dress strip
    # between the fronts widens toward the belt, so no single x is the front.
    inner_edge = np.full(H, np.inf)
    for y in np.nonzero(hull.any(1))[0]:
        inner_edge[y] = SX[y][hull[y]].min()
    upper = hull | ((SX >= inner_edge[:, None]) & (SX < 1.0) & (Y > 1.0) & (Y < BELT_TOP_HR))
    upper &= right_side_rule(SX, Y)
    foot_y, foot_x = seam_ys[-1], seam_xs[-1]
    hull_row = np.nonzero(hull[878 - 6])[0]
    hull_edge_at_belt = max(sign * (hull_row.min() - OX) / SC, sign * (hull_row.max() - OX) / SC)
    lower_side = (Y > foot_y) & (Y < BELT_TOP_HR + 0.02)
    t = np.clip((Y - foot_y) / (BELT_TOP_HR - foot_y), 0, 1)
    upper &= ~lower_side | (SX <= foot_x + (hull_edge_at_belt - foot_x) * t)

    lower = ndi.binary_fill_holes(lab == lower_id)
    a0 = [(np.nonzero(upper[y])[0].min(), np.nonzero(upper[y])[0].max()) for y in range(868, 878) if upper[y].any()]
    b0 = [(np.nonzero(lower[y])[0].min(), np.nonzero(lower[y])[0].max()) for y in range(927, 937)]
    a0, b0 = np.mean(a0, axis=0), np.mean(b0, axis=0)
    bridge = np.zeros(s.shape, bool)
    for y in range(874, 931):
        tt = (y - 874) / (931 - 874)
        lo, hi = (1 - tt) * a0 + tt * b0
        bridge[y, round(lo) : round(hi) + 1] = True
    piece = upper | bridge | lower
    piece = ndi.binary_fill_holes(ndi.binary_erosion(ndi.binary_dilation(piece, disk, 3), disk, 3))
    piece = ndi.binary_dilation(piece, disk, 3)
    pts = [((x - OX) / SC, (y - OY) / SC) for x, y in tl.boundary(piece)]
    start, segs = tl.fit_closed(pts, 0.008)
    result["jacket_" + side] = {"start": start, "segs": segs}
    d.line([(OX + x * SC, OY + y * SC) for x, y in tl.sample_chain(start, segs, 10)], fill="#00ff66", width=2)
    print("jacket", side, "segments", len(segs))

# --- the sleeve: its fitted edges from the joint down, the cap, the elbow's fill
cuff = ndi.binary_fill_holes(lab == 208)
band = (Y >= JY) & (Y <= 2.95) & (X >= np.polyval(in_line, Y)) & (X <= np.polyval(out_line, Y))
disc = (X - JX) ** 2 + (Y - JY) ** 2 <= RADIUS**2
ext = (sleeve & (Y >= 2.60)) | band | disc
ext |= ndi.binary_dilation(cuff, disk, 2) & ndi.binary_dilation(ext, disk, 6)
ext = ndi.binary_fill_holes(ndi.binary_erosion(ndi.binary_dilation(ext, disk, 3), disk, 3))
ext = ndi.binary_dilation(ext, disk, 3)
pts = [((x - OX) / SC, (y - OY) / SC) for x, y in tl.boundary(ext)]
start, segs = tl.fit_closed(pts, 0.008)
result["sleeve"] = {"start": start, "segs": segs}
d.line([(OX + x * SC, OY + y * SC) for x, y in tl.sample_chain(start, segs, 10)], fill="#ff2255", width=2)
d.ellipse((OX + (JX - RADIUS) * SC, OY + (JY - RADIUS) * SC, OX + (JX + RADIUS) * SC, OY + (JY + RADIUS) * SC), outline="#33aaff")
print("sleeve segments", len(segs))
json.dump(result, open(OUT / "shoulders.json", "w"), indent=1, default=float)
over.crop((340, 640, 960, 1080)).resize((1240, 880)).save(OUT / "shoulders_overlay.png")
