"""Hand contour lines, traced one by one and snapped onto the drawn dark line (same method as harness/franzi/ear_lines.py).

    ./harness/run.sh harness/franzi_hands/trace_lines.py view X0 Y0 X1 Y1 [ZOOM]
    ./harness/run.sh harness/franzi_hands/trace_lines.py emit

Each line is a short list of points read off a gridded zoom (flipped close-up px, see view.py), densified, and every sample slid along its normal
(within SNAP_R px) to the darkest point of a difference of Gaussians of the close-up. `view` prints, per line, how much of it lies on a dark ridge
against a control (the same curve shifted 14 px each side) and writes out/franzi/hand-lines-view.png. `emit` writes the lines, each with its
measured thickness, to out/franzi_hands/lines.json for the other scripts.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OUT = Path("out/franzi_hands")
SNAP_R = 7.0
SNAP_PEN = 0.5
ON_RIDGE = -18.0
W_MIN, W_MAX = 3.0, 16.0  # close-up px: the lines run 3 to 12 px thick there

# name: [(x, y), ...] in flipped close-up px, from the line's start outward
LINES: dict[str, list[tuple[float, float]]] = {
    # the outer long line: from the cavity's top corner down the edge of the lit hand to the long finger
    "edge": [(482, 800), (450, 825), (445, 885), (432, 945), (400, 990), (402, 1060), (407, 1110), (409, 1170), (450, 1255), (490, 1345), (540, 1407)],
    # from the kink beside it, down between the shaded fingers to the thumb's base
    "inner-a": [(412, 985), (430, 1030), (440, 1080), (452, 1117), (500, 1160), (550, 1197)],
    # the separation between the shaded finger pairs, from the edge line's bend out to the finger tips
    "sep": [(405, 1060), (407, 1100), (417, 1140), (430, 1175), (450, 1195), (500, 1240), (540, 1280), (565, 1302)],
}

img = np.array(Image.open("ref/franzi/hands/relaxed.png").convert("RGBA")).astype(float)[:, ::-1]
lum = img[..., :3].mean(2)
lum = np.where(img[..., 3] > 128, lum, 220.0)  # page counts as light, so the silhouette's edge is not a line
HP = ndimage.gaussian_filter(lum, 1.5) - ndimage.gaussian_filter(lum, 5.0)


def densify(pts, step=2.0):
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


def normals(c):
    t = np.gradient(ndimage.gaussian_filter1d(c, 4, axis=0, mode="nearest"), axis=0)
    t /= np.maximum(np.hypot(t[:, 0], t[:, 1]), 1e-9)[:, None]
    return np.stack([-t[:, 1], t[:, 0]], 1)


def at(c):
    return ndimage.map_coordinates(HP, [c[:, 1], c[:, 0]], order=1, mode="nearest")


def snap(pts):
    c = densify(pts)
    nrm = normals(c)
    offs = np.linspace(-SNAP_R, SNAP_R, 15)
    vals = np.stack([at(c + o * nrm) for o in offs], 1)
    best = ndimage.gaussian_filter1d(offs[np.argmin(vals + SNAP_PEN * np.abs(offs)[None, :], axis=1)], 4, mode="nearest")
    out = c + best[:, None] * nrm
    return out, best, at(out)


def width(out):
    """Thickness across the line at nine points: darkness coverage along the normal, between lit skin (212) and line (60)."""
    nrm = normals(out)
    res = []
    for i in np.linspace(0, len(out) - 1, 9).astype(int):
        offs = np.linspace(-14, 14, 57)
        v = ndimage.map_coordinates(lum, [out[i, 1] + offs * nrm[i, 1], out[i, 0] + offs * nrm[i, 0]], order=1, mode="nearest")
        res.append(float(np.clip((190 - v) / 130, 0, 1).sum() * (offs[1] - offs[0])))
    return ndimage.gaussian_filter1d(np.clip(res, W_MIN, W_MAX), 0.8, mode="nearest")


def report(name, pts):
    out, mv, on = snap(pts)
    n = normals(out)
    ctl = np.mean([at(out + s_ * n) < ON_RIDGE for s_ in (-14, 14)])
    print(f"{name:8s} len {np.hypot(*np.diff(out, axis=0).T).sum():6.0f}px  snap mean {np.abs(mv).mean():4.1f} max {np.abs(mv).max():4.1f}px  on a ridge {100 * (on < ON_RIDGE).mean():3.0f}% (control {100 * ctl:3.0f}%)  thickness {width(out).min():.1f}..{width(out).max():.1f}")
    return out


def view(box, zoom):
    im = Image.open("ref/franzi/hands/relaxed.png").convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    base = bg.convert("RGB").crop(box)
    base = base.resize((base.width * zoom, base.height * zoom), Image.LANCZOS)
    grid, drawn = base.copy(), base.copy()
    gd, dd = ImageDraw.Draw(grid), ImageDraw.Draw(drawn)
    for x in range((box[0] // 50 + 1) * 50, box[2], 50):
        gd.line([((x - box[0]) * zoom, 0), ((x - box[0]) * zoom, grid.height)], fill=(70, 120, 255), width=1)
        gd.text(((x - box[0]) * zoom + 2, 2), str(x), fill=(200, 0, 120))
    for y in range((box[1] // 50 + 1) * 50, box[3], 50):
        gd.line([(0, (y - box[1]) * zoom), (grid.width, (y - box[1]) * zoom)], fill=(70, 120, 255), width=1)
        gd.text((2, (y - box[1]) * zoom + 2), str(y), fill=(200, 0, 120))
    cols = [(255, 0, 80), (0, 160, 255), (0, 200, 60), (255, 160, 0), (160, 0, 220), (0, 180, 180)]
    for i, (name, pts) in enumerate(LINES.items()):
        out = report(name, pts)
        dd.line([((x - box[0]) * zoom, (y - box[1]) * zoom) for x, y in out], fill=cols[i % 6], width=3)
        for x, y in pts:
            X, Y = (x - box[0]) * zoom, (y - box[1]) * zoom
            dd.ellipse((X - 4, Y - 4, X + 4, Y + 4), outline=(0, 0, 0), width=1)
        X, Y = (pts[0][0] - box[0]) * zoom, (pts[0][1] - box[1]) * zoom
        dd.text((X + 6, Y - 12), name, fill=cols[i % 6])
    sheet = Image.new("RGB", (base.width * 2 + 16, base.height), "white")
    sheet.paste(grid, (0, 0))
    sheet.paste(drawn, (base.width + 16, 0))
    sheet.save("out/franzi/hand-lines-view.png")
    print("wrote out/franzi/hand-lines-view.png", sheet.size)


if __name__ == "__main__":
    if sys.argv[1] == "view":
        x0, y0, x1, y1 = map(int, sys.argv[2:6])
        view((x0, y0, x1, y1), int(sys.argv[6]) if len(sys.argv) > 6 else 2)
