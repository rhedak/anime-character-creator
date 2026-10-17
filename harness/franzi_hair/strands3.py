"""Franzi's strand lines, traced one by one on the highest-contrast view of the reference hair (contrast.py, variant C).

    ./harness/run.sh harness/franzi_hair/contrast.py                      # first: writes out/franzi/contrast-*.png
    ./harness/run.sh harness/franzi_hair/strands3.py view X0 Y0 X1 Y1 [ZOOM] [name,name,...]
    ./harness/run.sh harness/franzi_hair/strands3.py emit                 # writes out/franzi_hair/strands.json for emit.py

Why this exists: strands.py placed about a dozen lines by eye on a view where they could not be seen, and they did not follow the
reference's (the owner's read, checked on the stretched reference), and strands2.py's ridge detector finds only fragments. Here each
strand is a short list of points read off a gridded zoom of the stretched reference (reference canvas pixels, ref 04, 1312 x 2440),
then snapped: every sample of the smoothed curve slides along its normal, within SNAP_R px, to the darkest point of a difference of
Gaussians of the plain reference, so the curve sits on the drawn line and not where the eye guessed. `view` prints, per strand, how
far the snap moved it and how much of it lies on a dark ridge, which is the number to watch (a strand that needed a big move, or has
little of it on a ridge, was not placed on a real line).

`view` writes out/franzi/strand-view.png: the stretched reference of the box with a 20 px grid (to read coordinates off), and beside
it the same with the strands drawn on it (the snapped curve solid, your points as dots, the name at the start).
"""

import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OX, OY, S = 660.0, 270.5, 175.7
SNAP_R = 3.5
SNAP_PEN = 0.6  # cost per px of move, against the ridge value, so a point holds its place unless a ridge is clearly beside it
ON_RIDGE = -12.0  # difference-of-Gaussians value (on the 0 to 255 stretched view) under which a sample counts as on a drawn line

# name: [(x, y), ...] in reference canvas px, from the strand's start (at the whorl or the hairline) outward
STRANDS: dict[str, list[tuple[float, float]]] = {
    # tile 1: the whorl at (679, 158) and the upper right crown (view 640 80 780 240 6)
    "whorl-up": [(680, 152), (681.7, 143.3), (687.5, 130), (690, 116.7), (690, 105), (687.5, 95), (684.7, 90)],
    "lobe-right": [(680, 155), (682.5, 148.3), (691.7, 136.7), (703.3, 130), (713.3, 123.7), (718.3, 113.3), (718.7, 96.7)],
    "lobe-left": [(679.2, 150), (679.5, 135), (677.5, 121.7), (673.3, 110), (666.7, 98.3), (660.8, 90)],
    "fan-1": [(675, 136.7), (665, 125), (653.3, 115.8), (640, 108.3), (634, 106.8), (617, 102), (602, 102)],
    "fan-2": [(677.5, 146.7), (668.3, 136.7), (655, 127.5), (640, 124.2), (630, 121.5), (617, 119), (597, 121), (582, 127)],
    "fan-3": [(675.8, 158.3), (666.7, 150), (655, 143.3), (640, 140.8), (624.8, 144), (612.8, 150), (600.8, 160), (590.8, 174), (580.8, 190), (574.8, 206), (568.8, 222), (564.8, 242), (562.8, 258), (561, 285), (559.8, 310)],
    # tile 3: the left crown (view 500 70 680 270 5)
    "crown-L3": [(636.8, 128), (622.8, 130), (606.8, 136), (590.8, 146), (578.8, 156), (566.8, 170), (556.8, 184), (546.8, 200), (540.8, 218), (536.8, 242), (534.8, 266), (537.5, 275), (538.8, 308)],
    "lock-B": [(552.8, 260), (553.3, 290), (553.8, 322)],
    # thin oblique lines between that arc and the left silhouette (view 505 130 585 260 8)
    "edge-1": [(541.8, 167.5), (550, 162), (558, 156), (566.8, 150.6)],
    "edge-3": [(523, 212.5), (535.5, 205), (546.8, 195)],
    "edge-4": [(519, 250), (524, 240), (530, 229)],
    "fan-4": [(673.3, 175), (661.7, 166.7), (650, 161.7), (640, 165)],
    "arc-short": [(683.7, 158.3), (690, 156.3), (698.3, 155.3), (710, 158.3), (718.3, 166.7)],
    "sweep": [(685, 148.3), (695, 144.2), (706.7, 142.5), (723.3, 148.3), (740, 163.3), (753.3, 181.7), (763.3, 200), (769, 223.3), (770.8, 228.3), (775.8, 243.3), (778.3, 258.3), (779.5, 278.3), (780, 300), (780.5, 320), (778, 345), (774.5, 366), (769.2, 386), (764, 398.3), (761.7, 408), (759, 415), (755.7, 430), (749, 443.3), (740.7, 458.3), (734, 468)],
    "upper-lobe": [(697.5, 135), (706.7, 128.7), (720, 124.2), (733.3, 122.5), (746.7, 121.7), (756.7, 124.7), (765, 131.7)],
    "lobe-low": [(738, 172), (747, 177), (756.5, 178.3), (767.3, 175), (774, 163.3), (775.7, 150)],
    # tile 2: the curtain (view 680 150 820 330 6)
    "wedge-left": [(731, 192.2), (736.1, 203.3), (741.7, 216.7), (746.1, 227.8), (749.5, 241), (753.5, 255), (758, 268), (762, 280)],
    "lobe-low2": [(758.3, 191.7), (770, 198.3), (781.7, 197.5), (788.3, 188.3), (789.2, 175)],
    # tile 5: below the ear, where two strands cross into the ponytail (view 735 220 835 420 5)
    "tail-S2": [(776, 365), (774.8, 380), (775, 396), (783.8, 408), (788, 420), (793.3, 426.7), (798.3, 431.7), (806, 440), (814, 450)],
    # tile 6: the ponytail (view 715 360 835 530 6)
    "pony-1": [(771.5, 418.3), (775.7, 431.7), (775.7, 445), (772.3, 461.7), (765.7, 480), (762.3, 490)],
    "pony-2": [(786.5, 425), (789.8, 438.3), (790.7, 453.3), (788.2, 466.7), (780.7, 480), (777.3, 491.7)],
    "pony-3": [(797.3, 466.7), (795.7, 476.7), (792.3, 486.7), (787.3, 496.7)],
    "pony-4": [(766.5, 441.7), (766.5, 453.3), (765.7, 465), (764.8, 471.7)],
    "pony-5": [(761.5, 441.7), (760.7, 455), (758.2, 466.7), (755.7, 475)],
    "outer-R1": [(784, 284), (790, 268), (796, 254), (800, 246)],
    "outer-R2": [(791, 284), (797, 272), (802, 260)],
    "lobe-low3": [(784.8, 160), (785.7, 171.7), (791, 190), (794.8, 198), (794, 206), (789, 215), (776.5, 228.3), (770, 233)],
}

# The ridge is measured on the stretched view the lines are read from (contrast.py, C), not on the plain reference: a dark line on
# near-black hair differs from its surroundings by a few levels there, and the first version of this measure called a correctly
# placed strand 25% on a ridge for that reason.
_lum = np.array(Image.open("out/franzi/contrast-C.png").convert("L")).astype(float)
HP = ndimage.gaussian_filter(_lum, 0.9) - ndimage.gaussian_filter(_lum, 3.0)
HAIR_INNER = ndimage.binary_erosion(ndimage.binary_fill_holes(np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/black-hair.png"))[..., 3] > 128), iterations=3)


def densify(pts, step=1.0):
    """Catmull-Rom through the points (ends repeated), sampled about every `step` px."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        seg = np.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1])
        n = max(2, int(seg / step))
        for k in range(n):
            t = k / n
            out.append(
                [
                    0.5 * ((2 * p[i][j]) + (-p[i - 1][j] + p[i + 1][j]) * t + (2 * p[i - 1][j] - 5 * p[i][j] + 4 * p[i + 1][j] - p[i + 2][j]) * t**2 + (-p[i - 1][j] + 3 * p[i][j] - 3 * p[i + 1][j] + p[i + 2][j]) * t**3)
                    for j in (0, 1)
                ]
            )
    out.append(list(pts[-1]))
    return np.array(out, float)


def snap(pts):
    """The densified curve slid along its normal onto the nearest dark ridge. Returns (curve, move per sample, ridge value per sample)."""
    c = densify(pts)
    t = np.gradient(ndimage.gaussian_filter1d(c, 4, axis=0, mode="nearest"), axis=0)
    t /= np.maximum(np.hypot(t[:, 0], t[:, 1]), 1e-9)[:, None]
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    offs = np.linspace(-SNAP_R, SNAP_R, 15)
    vals = np.stack([ndimage.map_coordinates(HP, [c[:, 1] + o * nrm[:, 1], c[:, 0] + o * nrm[:, 0]], order=1, mode="nearest") for o in offs], 1)
    best = offs[np.argmin(vals + SNAP_PEN * np.abs(offs)[None, :], axis=1)]
    best = ndimage.gaussian_filter1d(best, 3, mode="nearest")
    out = c + best[:, None] * nrm
    on = ndimage.map_coordinates(HP, [out[:, 1], out[:, 0]], order=1, mode="nearest")
    return out, best, on


def report(name, pts):
    out, mv, on = snap(pts)
    length = float(np.hypot(*np.diff(out, axis=0).T).sum())
    # the control: the same curve moved 8 px to each side, which is what "on a ridge" has to beat
    t = np.gradient(ndimage.gaussian_filter1d(out, 4, axis=0, mode="nearest"), axis=0)
    t /= np.maximum(np.hypot(t[:, 0], t[:, 1]), 1e-9)[:, None]
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    ctl = []
    for s in (-8, 8):
        q = out + s * nrm
        ctl.append(ndimage.map_coordinates(HP, [q[:, 1], q[:, 0]], order=1, mode="nearest") < ON_RIDGE)
    print(f"{name:14s} len {length:6.1f}px  snap mean {np.abs(mv).mean():3.1f} max {np.abs(mv).max():3.1f}px  on a ridge {100 * (on < ON_RIDGE).mean():3.0f}%  (control {100 * np.mean(ctl):3.0f}%)")
    return out


def view(box, zoom, only):
    base = Image.open("out/franzi/contrast-C.png").convert("RGB").crop(box)
    base = base.resize((base.width * zoom, base.height * zoom), Image.LANCZOS)
    grid = base.copy()
    gd = ImageDraw.Draw(grid)
    for x in range((box[0] // 20 + 1) * 20, box[2], 20):
        X = (x - box[0]) * zoom
        gd.line([(X, 0), (X, grid.height)], fill=(70, 120, 255) if x % 100 else (255, 160, 0), width=1)
        gd.text((X + 2, 2), str(x), fill=(255, 255, 0))
    for y in range((box[1] // 20 + 1) * 20, box[3], 20):
        Y = (y - box[1]) * zoom
        gd.line([(0, Y), (grid.width, Y)], fill=(70, 120, 255) if y % 100 else (255, 160, 0), width=1)
        gd.text((2, Y + 2), str(y), fill=(255, 255, 0))
    drawn = base.copy()
    # the residual: dark ridges inside the hair that no strand covers yet, in green, so a line that was missed shows by itself
    near = np.zeros(HP.shape, bool)
    for pts in STRANDS.values():
        ij = np.round(snap(pts)[0]).astype(int)
        near[ij[:, 1].clip(0, HP.shape[0] - 1), ij[:, 0].clip(0, HP.shape[1] - 1)] = True
    near = ndimage.binary_dilation(near, iterations=4)
    resid = (HP < ON_RIDGE) & (_lum < 90) & HAIR_INNER & ~near  # dark itself: the edge of a white highlight also dips, and is not a line
    rc = np.array(Image.fromarray(resid[box[1] : box[3], box[0] : box[2]].astype(np.uint8) * 255).resize(drawn.size, Image.NEAREST)) > 0
    arr = np.array(drawn)
    arr[rc] = (0, 255, 90)
    drawn = Image.fromarray(arr)
    dd = ImageDraw.Draw(drawn)
    colours = [(255, 30, 30), (255, 230, 0), (0, 235, 255), (80, 255, 0), (255, 0, 230), (255, 140, 0)]
    for i, (name, pts) in enumerate(STRANDS.items()):
        if only and name not in only:
            continue
        col = colours[i % len(colours)]
        out = report(name, pts)
        dd.line([((x - box[0]) * zoom, (y - box[1]) * zoom) for x, y in out], fill=col, width=2)
        for x, y in pts:
            X, Y = (x - box[0]) * zoom, (y - box[1]) * zoom
            dd.ellipse((X - 3, Y - 3, X + 3, Y + 3), outline=(255, 255, 255), width=1)
        X, Y = (pts[0][0] - box[0]) * zoom, (pts[0][1] - box[1]) * zoom
        dd.text((X + 5, Y - 12), name, fill=col)
    sheet = Image.new("RGB", (base.width * 2 + 16, base.height), "white")
    sheet.paste(grid, (0, 0))
    sheet.paste(drawn, (base.width + 16, 0))
    sheet.save("out/franzi/strand-view.png")
    print("wrote out/franzi/strand-view.png", sheet.size)


def emit():
    chains = []
    for name, pts in STRANDS.items():
        out, _, _ = snap(pts)
        chains.append([[(x - OX) / S, (y - OY) / S] for x, y in out[::3]])
    json.dump(chains, open("out/franzi_hair/strands.json", "w"))
    print("wrote out/franzi_hair/strands.json,", len(chains), "strands")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "view":
        x0, y0, x1, y1 = map(int, sys.argv[2:6])
        z = int(sys.argv[6]) if len(sys.argv) > 6 else 4
        only = set(sys.argv[7].split(",")) if len(sys.argv) > 7 else set()
        view((x0, y0, x1, y1), z, only)
    elif cmd == "emit":
        emit()
