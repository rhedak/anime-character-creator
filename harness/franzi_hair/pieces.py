"""Cut Franzi's hair layer into pieces and trace each on its own (trace-reference skill), because one smoothed outline destroys the
thin parts. Pieces, all in head radii (the calibration of trace.py): `dome` (the skull's hair, closed behind the face), `left`
(the long lock down the viewer's left) and `tail` (the curtain down the viewer's right, which runs into the ponytail).

    ./harness/run.sh harness/franzi_hair/face_trace.py
    ./harness/run.sh harness/franzi_hair/pieces.py

Writes out/franzi_hair/pieces.json and out/franzi_hair/pieces.png (the cut, on the contrast-stretched hair).
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
raw = ndimage.binary_fill_holes(np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/black-hair.png"))[..., 3] > 128)
hair = ndimage.binary_erosion(raw, iterations=ERODE)
head = np.load(OUT / "head_mask.npy")
yy, xx = np.mgrid[0 : hair.shape[0], 0 : hair.shape[1]]
X, Y = (xx - OX) / S, (yy - OY) / S

# The cut: below the temple the hair is a free lock on each side
# The head skin the trace carries out to the hair's outer edge (everything inside the hair, ears included) is hair in the picture,
# so the free pieces take it too, and draw over it.
face = np.load(OUT / "face_mask.npy")
layer = hair | (head & ~ndimage.binary_dilation(face, iterations=2))
left = layer & (((X < -0.5) & (Y > -0.3)) | ((X < -0.15) & (Y > 0.6)))
tail = layer & (((X > 0.5) & (Y > -0.3)) | ((X > 0.15) & (Y > 0.6)))
# The dome is the whole skull down to the jaw line, the pieces' tops included (they are drawn over it); only below the temples
# does it stop, so the thin locks and the ponytail keep their own outlines.
# Keep the free pieces off the eyes: in the eye band (0 to 0.5 radii below the head centre) they start at 0.6 radii, past the outer
# corner of the eye; the face's own edge does the rest below it.
band = (np.abs(X) < 0.6) & (Y > -0.05) & (Y < 0.5)
left, tail = left & ~band, tail & ~band
dome = ((hair | head | left | tail) & (Y < 0.6)) | head
# the free pieces overlap the dome by a few pixels so no hairline of page shows between them
left_d, tail_d = ndimage.binary_dilation(left, iterations=4), ndimage.binary_dilation(tail, iterations=4)
dome = ndimage.binary_fill_holes(ndimage.binary_closing(dome, iterations=3))


def to_r(pts):
    return [((x - OX) / S, (y - OY) / S) for x, y in pts]


def fit(mask, tol, blur):
    m = ndimage.gaussian_filter(mask.astype(float), blur) > 0.5 if blur else mask
    return tl.fit_closed(to_r(tl.boundary(m)), tol)


res = {
    "dome": fit(dome, 0.012, 1.5),
    "left": fit(left_d, 0.012, 2.2),  # thin: moderate smoothing, so its point survives
    "tail": fit(tail_d, 0.016, 4.0),
}
json.dump(res, open(OUT / "pieces.json", "w"), default=lambda o: list(o), indent=1)
for k, (st, sg) in res.items():
    print(k, "segments", len(sg))
# the cut over the contrast-stretched hair, for checking
a = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")).astype(float)
st = np.clip((a[..., :3].mean(2) - 8) / 100, 0, 1)
rgb = np.stack([st, st, st], 2) * 255
for m, c in ((dome, (90, 140, 255)), (left, (255, 120, 40)), (tail, (60, 200, 90))):
    rgb[m] = 0.45 * rgb[m] + 0.55 * np.array(c)
Image.fromarray(rgb.astype(np.uint8)).crop((480, 60, 880, 560)).resize((800, 1000), Image.LANCZOS).save(OUT / "pieces.png")
