"""Trace Franzi's hair (trace-reference skill, steps 2 to 4) into chains in head radii.

    ./harness/run.sh harness/franzi_hair/face_trace.py     # first: writes the head and face masks
    ./harness/run.sh harness/franzi_hair/trace.py

Source: ref/franzi/segments/04-bikini-fullbody/black-hair.png (the hair layer, registered to the composite). Calibration
(docs/adult-body-status.md): the body gate maps the figure onto ours at 175.7 reference px per head radius; origin x 660 (eye
midpoint and chin tip), origin y 270.5 (the drawn chin, 455 px, is 1.05 radii below it). The mask is eroded 3 px so the
traced line sits on the centre of our stroke, not on the reference's outer ink edge.

The hair is one shape drawn over the head. One closed chain, `mass`, is the outline of the hair joined with the head
(closed across the face opening by the jaw). The hairline is the hair's inner edge against the face opening; its two ends
are marks of `mass`, so the front piece (hairline, then `mass` the long way round the top) shares its silhouette with the
mass exactly and nothing doubles. Writes out/franzi_hair/chains.json: mass, line, seam indices.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, "/Users/henrik/git/anime-character-creator/.claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/franzi_hair")
OX, OY, S = 660.0, 270.5, 175.7
ERODE = 3
TOL = 0.012

hair = ndimage.binary_erosion(ndimage.binary_fill_holes(np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/black-hair.png"))[..., 3] > 128), iterations=ERODE)
head = np.load(OUT / "head_mask.npy")
face = np.load(OUT / "face_mask.npy")
# The layer's edge is ragged (it is a segmented AI image), and the strand tips make notches: smooth both masks before tracing,
# and close the small hollows between the ponytail and the neck, where the reference's hair meets the shoulder.
# The mass is the dome only: the two long locks are traced as their own pieces (pieces.py) and drawn over it. One smoothed
# outline for all of it rounded the thin lock into a stub.
yy_, xx_ = np.mgrid[0 : hair.shape[0], 0 : hair.shape[1]]
X_, Y_ = (xx_ - OX) / S, (yy_ - OY) / S
_face = np.load(OUT / "face_mask.npy")
_layer = hair | (head & ~ndimage.binary_dilation(_face, iterations=2))
left_ = _layer & (((X_ < -0.5) & (Y_ > -0.3)) | ((X_ < -0.15) & (Y_ > 0.6)))
tail_ = _layer & (((X_ > 0.5) & (Y_ > -0.3)) | ((X_ > 0.15) & (Y_ > 0.6)))
hair = ndimage.gaussian_filter((hair & ~left_ & ~tail_).astype(float), 1.5) > 0.5
mass_mask = ndimage.binary_closing(hair | head, iterations=3)


def to_r(pts):
    return [((x - OX) / S, (y - OY) / S) for x, y in pts]


hb = tl.boundary(hair)  # the hair's own contour, in order
near_face = ndimage.binary_dilation(face, iterations=14)
flag = [bool(near_face[y, x]) for x, y in hb]
# contiguous runs of hairline pixels around the loop
runs, cur = [], []
for i, f in enumerate(flag):
    if f:
        cur.append(i)
    elif cur:
        runs.append(cur)
        cur = []
if cur:
    if runs and flag[0]:
        runs[0] = cur + runs[0]
    else:
        runs.append(cur)
runs.sort(key=len, reverse=True)
print("hair contour", len(hb), "hairline runs", [len(r) for r in runs[:4]])
for r in sorted(runs, key=lambda r: r[0]):
    if len(r) > 15:
        print("  run idx", r[0], r[-1], "len", len(r), "from", [round(v, 2) for v in to_r([hb[r[0]]])[0]], "to", [round(v, 2) for v in to_r([hb[r[-1]]])[0]])
# The hairline is the whole stretch from the first run to the last (the gaps between runs are where the face mask
# retreats from the hair, not breaks in the line).
first, last = min(r[0] for r in runs if len(r) > 15), max(r[-1] for r in runs if len(r) > 15)
line_pts = hb[first : last + 1]
print("hairline from", [round(v, 2) for v in to_r([line_pts[0]])[0]], "to", [round(v, 2) for v in to_r([line_pts[-1]])[0]], "pixels", len(line_pts))
lxy = to_r(line_pts)
lstart, lsegs = tl.fit_chain(lxy, tl.simplify(lxy, TOL))

mb = tl.boundary(mass_mask)


def nearest(p):
    return min(range(len(mb)), key=lambda i: (mb[i][0] - p[0]) ** 2 + (mb[i][1] - p[1]) ** 2)


i_start, i_end = nearest(line_pts[0]), nearest(line_pts[-1])  # beside the line's start and end, on the mass
loop = mb[i_end:] + mb[:i_end]  # begin at the seam beside the line's END, the left side
j = (i_start - i_end) % len(mb)
xy = to_r(loop) + [to_r(loop)[0]]
marks = sorted(set(tl.simplify(xy[: j + 1], TOL)) | set(j + i for i in tl.simplify(xy[j:], TOL)) | {0, j})
mstart, msegs = tl.fit_chain(xy, marks)
k = marks.index(j)
top, rest_arc = msegs[:k], msegs[k:]
pts_top = tl.sample_chain(mstart, top, 6)
mean_top = float(np.mean([p[1] for p in pts_top]))
print("arc from the left seam to the right seam: mean y", round(mean_top, 3), "(it runs over the top and down the ponytail)", "segments", len(top), "of", len(msegs))
ys_top = [q[1] for q in pts_top]
print("top arc reaches y", round(min(ys_top), 3), "to", round(max(ys_top), 3))
assert min(ys_top) < -1.0, "this arc does not run over the top"
res = {
    "mass": (mstart, msegs),
    "top_segments": k,
    "line": (lstart, lsegs),
}
json.dump(res, open(OUT / "chains.json", "w"), default=lambda o: list(o), indent=1)
print("mass segments", len(msegs), "line segments", len(lsegs), "seam left", [round(v, 3) for v in mstart], "seam right", [round(v, 3) for v in top[-1][1]])
print("line start", [round(v, 3) for v in lstart], "line end", [round(v, 3) for v in lsegs[-1][1]])
