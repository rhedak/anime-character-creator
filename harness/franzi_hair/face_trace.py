"""Trace Franzi's head and ears from the composite (trace-reference skill) into chains in head radii.

    ./harness/run.sh harness/franzi_hair/face_trace.py

The head is the skin of the face (closed over the eyes and brows) joined above the jaw with everything inside the hair, so
the hair drawn over it never lets the page show; below that its edge is the visible jaw and chin. It is made symmetric from
its right half (the left is more hidden by hair). The right ear is traced from its skin component and mirrored. Same
calibration as trace.py; grown by 3 px so the line lands on the centre of our stroke. Writes out/franzi_hair/face.json
(head, ear_r, ear_l: closed chains in head radii).
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
JAW_R = 0.55  # below this many radii (below the head centre) the head's edge is the visible jaw, above it the hair's inside

im = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA"))
rgb = im[..., :3].astype(int)
skin = (np.abs(rgb - [0xFF, 0xD0, 0xB5]).sum(2) < 70) & (im[..., 3] > 128)
skin[560:] = False
lab, _ = ndimage.label(ndimage.binary_closing(skin, iterations=1))


def component(x, y):
    ys, xs = np.nonzero(lab)
    i = int(np.argmin((xs - x) ** 2 + (ys - y) ** 2))
    return lab == lab[ys[i], xs[i]]


def to_r(pts):
    return [((x - OX) / S, (y - OY) / S) for x, y in pts]


yy, xx = np.mgrid[0 : im.shape[0], 0 : im.shape[1]]
yr = (yy - OY) / S
hair = ndimage.binary_fill_holes(np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/black-hair.png"))[..., 3] > 128)
face = ndimage.binary_fill_holes(ndimage.binary_closing(component(660, 330), iterations=10))
# Only as wide as the face (0.62 radii): the hair beside it is the hair's, drawn by the cut's mass and its free pieces.
inside_hair = ndimage.binary_fill_holes(hair | face) & (yr < JAW_R) & (np.abs((xx - OX) / S) < 0.62)
head = ndimage.binary_dilation(face | inside_hair, iterations=3)
np.save(OUT / "face_mask.npy", face)
np.save(OUT / "head_mask.npy", head)
pts = to_r(tl.boundary(head))
# Symmetric: walk the boundary from its topmost point to its lowest, keep that half's x as |x|, mirror it back up.
k0 = min(range(len(pts)), key=lambda i: (pts[i][1], abs(pts[i][0])))
loop = pts[k0:] + pts[:k0]
kc = max(range(len(loop)), key=lambda i: loop[i][1])
sides = [loop[: kc + 1], loop[kc:]]
right = [s for s in sides if np.mean([p[0] for p in s]) > 0][0]
right = right if right[0][1] < right[-1][1] else right[::-1]  # top to chin
half = [(abs(x), y) for x, y in right]
full = half + [(-x, y) for x, y in reversed(half[1:-1])]
xs = [p[0] for p in full]; ys = [p[1] for p in full]
print("head extent x", round(min(xs), 3), round(max(xs), 3), "y", round(min(ys), 3), round(max(ys), 3))
out = {"head": tl.fit_closed(full, 0.012)}


def symmetric_chain(mask, tol):
    pts_ = to_r(tl.boundary(ndimage.binary_dilation(mask, iterations=3)))
    k0_ = min(range(len(pts_)), key=lambda i: (pts_[i][1], abs(pts_[i][0])))
    lp = pts_[k0_:] + pts_[:k0_]
    kc_ = max(range(len(lp)), key=lambda i: lp[i][1])
    sd = [lp[: kc_ + 1], lp[kc_:]]
    rt = [q for q in sd if np.mean([p_[0] for p_ in q]) > 0][0]
    rt = rt if rt[0][1] < rt[-1][1] else rt[::-1]
    hf = [(abs(x), y) for x, y in rt]
    return tl.fit_closed(hf + [(-x, y) for x, y in reversed(hf[1:-1])], tol)


# The face's own skin, with no hair interior: its top edge is the hairline, its sides the face's edge, its foot the jaw.
# The eyes are dark, so the face skin has deep notches round them, and the outline stroke ran along each lid, doubling it. Fill the
# face across each row between its outermost pixels (rows 240 to 400 of the reference: brow to below the eyes), so the outline
# follows the face's real edge; the eyes, brows and lids are drawn over the skin.
closed = ndimage.binary_closing(face, iterations=3)
filled = closed.copy()
for yy_ in range(240, 400):
    xs_ = np.nonzero(closed[yy_])[0]
    if len(xs_):
        filled[yy_, xs_.min() : xs_.max() + 1] = True
out["face"] = symmetric_chain(filled, 0.01)
print("face segments", len(out["face"][1]))
print("head segments", len(out["head"][1]))

ear = ndimage.binary_dilation(ndimage.binary_fill_holes(ndimage.binary_closing(component(790, 335), iterations=4)), iterations=3)
epts = to_r(tl.boundary(ear))
exs = [p[0] for p in epts]; eys = [p[1] for p in epts]
print("ear_r extent x", round(min(exs), 3), round(max(exs), 3), "y", round(min(eys), 3), round(max(eys), 3), "pixels", int(ear.sum()))
out["ear_r"] = tl.fit_closed(epts, 0.01)
start, segs = out["ear_r"]
out["ear_l"] = ([-start[0], start[1]], [[[-c[0], c[1]], [-e[0], e[1]]] for c, e in segs])
json.dump(out, open(OUT / "face.json", "w"), default=lambda o: list(o), indent=1)
