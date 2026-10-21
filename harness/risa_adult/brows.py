"""Risa's two brows: thin dark lines across the fringe, read off gridded zooms of the reference and snapped onto the drawn line.

    ./harness/run.sh harness/risa_adult/brows.py [view]

The method is harness/franzi_hair/strands3.py's: each brow is a short list of points in reference pixels, the Catmull-Rom curve through them
slides along its normal, within SNAP_R px, to the darkest point of a difference of Gaussians of the reference, and the result is fitted as a
quadratic chain in head radii. `view` writes out/risa_adult/brows-view.png (the box at 6x, the snapped lines over it). The bare run writes
out/risa_adult/brows.json: {"chains": [chain, ...], "widths": [[head radii at each fitted point...], ...]} for outline_trace.py.

The widths are what is measured across each line (a brow is 1.5 to 2.5 px thick, tapering to nothing at both ends).
"""

import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OX, OY, S = 660.0, 270.5, 175.7
SNAP_R = 2.5
lum = np.array(Image.open("ref/risa-adult/00-bikini.png").convert("RGB")).astype(float).mean(2)
HP = ndimage.gaussian_filter(lum, 0.8) - ndimage.gaussian_filter(lum, 2.5)

# reference px, from the outer end toward the nose for the viewer's left brow and from the nose out for the right (the same order as the mirrored traces of Franzi)
BROWS = {
    "left": [(571, 283), (580, 278), (590, 274), (602, 271), (614, 269), (626, 269), (636, 270), (645, 272)],
    "right": [(686, 269), (693, 265), (702, 261), (713, 259), (724, 259), (735, 261), (746, 264), (758, 268), (770, 272)],
}
WIDTH = [0.6, 1.4, 1.9, 2.1, 2.1, 1.9, 1.6, 1.2, 0.5]  # px along each line, resampled to its length


def densify(pts, step=1.0):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        seg = np.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1])
        n = max(2, int(seg / step))
        for k in range(n):
            t = k / n
            out.append([0.5 * ((2 * p[i][j]) + (-p[i - 1][j] + p[i + 1][j]) * t + (2 * p[i - 1][j] - 5 * p[i][j] + 4 * p[i + 1][j] - p[i + 2][j]) * t**2 + (-p[i - 1][j] + 3 * p[i][j] - 3 * p[i + 1][j] + p[i + 2][j]) * t**3) for j in (0, 1)])
    out.append(list(pts[-1]))
    return np.array(out, float)


def snap(pts):
    c = densify(pts)
    t = np.gradient(ndimage.gaussian_filter1d(c, 3, axis=0, mode="nearest"), axis=0)
    t /= np.maximum(np.hypot(t[:, 0], t[:, 1]), 1e-9)[:, None]
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    offs = np.linspace(-SNAP_R, SNAP_R, 11)
    vals = np.stack([ndimage.map_coordinates(HP, [c[:, 1] + o * nrm[:, 1], c[:, 0] + o * nrm[:, 0]], order=1, mode="nearest") for o in offs], 1)
    best = ndimage.gaussian_filter1d(offs[np.argmin(vals + 0.5 * np.abs(offs)[None, :], axis=1)], 3, mode="nearest")
    return c + best[:, None] * nrm, best


if len(sys.argv) > 1 and sys.argv[1] == "view":
    box, z = (550, 245, 800, 300), 6
    base = Image.open("ref/risa-adult/00-bikini.png").convert("RGB").crop(box).resize(((box[2] - box[0]) * z, (box[3] - box[1]) * z), Image.LANCZOS)
    d = ImageDraw.Draw(base)
    for name, pts in BROWS.items():
        out, mv = snap(pts)
        print(f"{name:6s} snap mean {np.abs(mv).mean():.2f} max {np.abs(mv).max():.2f} px, length {np.hypot(*np.diff(out, axis=0).T).sum():.0f} px")
        d.line([((x - box[0]) * z, (y - box[1]) * z) for x, y in out], fill=(0, 255, 255), width=1)
    base.save("out/risa_adult/brows-view.png")
    print("wrote out/risa_adult/brows-view.png", base.size)
else:
    chains, widths = [], []
    for name, pts in BROWS.items():
        out, _ = snap(pts)
        r = [((x - OX) / S, (y - OY) / S) for x, y in out[::2]]
        ch = tl.fit_chain(r, tl.simplify(r, 0.004))
        chains.append(ch)
        # the width at each fitted point: interpolated along the arc, in head radii
        n_pts = 1 + len(ch[1])
        widths.append([float(np.interp(i / (n_pts - 1), np.linspace(0, 1, len(WIDTH)), WIDTH)) / S for i in range(n_pts)])
    json.dump({"chains": chains, "widths": widths}, open("out/risa_adult/brows.json", "w"), default=lambda o: list(o))
    print("wrote out/risa_adult/brows.json")
