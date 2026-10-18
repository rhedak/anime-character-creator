"""The fold lines inside Franzi's ears, traced one by one and snapped onto the drawn dark line.

    ./harness/run.sh harness/franzi_hair/ear_lines.py view r|l [ZOOM]
    ./harness/run.sh harness/franzi_hair/ear_lines.py emit        # writes ts/src/body-adult-ear-data.ts

Same method as strands3.py: each line is a short list of points read off a gridded zoom (reference canvas px, ref 04), densified, and
every sample slid along its normal (within SNAP_R px) to the darkest point of a difference of Gaussians of the plain reference. The
ear's fold lines are dark brown on tan (luminance 13 to 80 against 150 to 205), so unlike the hair the plain image is enough. `view`
prints, per line, how much of it lies on a dark ridge against a control (the same curve shifted 6 px each side).
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OX, OY, S = 660.0, 270.5, 175.7
SNAP_R = 2.5
SNAP_PEN = 0.5
ON_RIDGE = -25.0

# name: (ear, [(x, y), ...]) from the line's start outward, reference canvas px
LINES: dict[str, tuple[str, list[tuple[float, float]]]] = {
    # right ear (view r): the dark fold that runs from the lock up over the apex of the shaded upper part
    "r-fold-upper": ("r", [(781.3, 312.9), (782.9, 309.2), (786.3, 305.8), (790.0, 304.2), (792.1, 304.3), (793.8, 306.3)]),
    # the arc that bounds the shaded lower part on its right and swings back to the lock
    "r-fold-arc": ("r", [(781.7, 320.8), (785.8, 325.0), (787.5, 331.7), (787.9, 336.7), (786.3, 341.7), (782.9, 345.4), (778.8, 347.5)]),
    # left ear (view l): the short dark stroke at the top of the shaded part
    "l-fold": ("l", [(534.3, 319.3), (536.0, 320.0), (537.7, 321.5)]),
}

_lum = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")).astype(float)[..., :3].mean(2)
HP = ndimage.gaussian_filter(_lum, 0.7) - ndimage.gaussian_filter(_lum, 2.5)


def densify(pts, step=0.5):
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
    t = np.gradient(ndimage.gaussian_filter1d(c, 2, axis=0, mode="nearest"), axis=0)
    t /= np.maximum(np.hypot(t[:, 0], t[:, 1]), 1e-9)[:, None]
    return np.stack([-t[:, 1], t[:, 0]], 1)


def at(c):
    return ndimage.map_coordinates(HP, [c[:, 1], c[:, 0]], order=1, mode="nearest")


def snap(pts):
    c = densify(pts)
    nrm = normals(c)
    offs = np.linspace(-SNAP_R, SNAP_R, 11)
    vals = np.stack([at(c + o * nrm) for o in offs], 1)
    best = ndimage.gaussian_filter1d(offs[np.argmin(vals + SNAP_PEN * np.abs(offs)[None, :], axis=1)], 2, mode="nearest")
    out = c + best[:, None] * nrm
    return out, best, at(out)


def report(name, pts):
    out, mv, on = snap(pts)
    n = normals(out)
    ctl = np.mean([at(out + s * n) < ON_RIDGE for s in (-6, 6)])
    print(f"{name:14s} len {np.hypot(*np.diff(out, axis=0).T).sum():5.1f}px  snap mean {np.abs(mv).mean():3.1f} max {np.abs(mv).max():3.1f}px  on a ridge {100 * (on < ON_RIDGE).mean():3.0f}% (control {100 * ctl:3.0f}%)")
    return out


def view(which, zoom):
    box = (765, 285, 825, 375) if which == "r" else (515, 295, 575, 375)
    im = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    base = bg.convert("RGB").crop(box)
    base = base.resize((base.width * zoom, base.height * zoom), Image.LANCZOS)
    grid, drawn = base.copy(), base.copy()
    gd, dd = ImageDraw.Draw(grid), ImageDraw.Draw(drawn)
    for x in range((box[0] // 10 + 1) * 10, box[2], 10):
        gd.line([((x - box[0]) * zoom, 0), ((x - box[0]) * zoom, grid.height)], fill=(70, 120, 255), width=1)
        gd.text(((x - box[0]) * zoom + 2, 2), str(x), fill=(200, 0, 120))
    for y in range((box[1] // 10 + 1) * 10, box[3], 10):
        gd.line([(0, (y - box[1]) * zoom), (grid.width, (y - box[1]) * zoom)], fill=(70, 120, 255), width=1)
        gd.text((2, (y - box[1]) * zoom + 2), str(y), fill=(200, 0, 120))
    colours = [(255, 0, 80), (0, 160, 255), (0, 200, 60)]
    for i, (name, (ear, pts)) in enumerate(LINES.items()):
        if ear != which:
            continue
        out = report(name, pts)
        dd.line([((x - box[0]) * zoom, (y - box[1]) * zoom) for x, y in out], fill=colours[i % 3], width=2)
        for x, y in pts:
            X, Y = (x - box[0]) * zoom, (y - box[1]) * zoom
            dd.ellipse((X - 3, Y - 3, X + 3, Y + 3), outline=(0, 0, 0), width=1)
    sheet = Image.new("RGB", (base.width * 2 + 16, base.height), "white")
    sheet.paste(grid, (0, 0))
    sheet.paste(drawn, (base.width + 16, 0))
    sheet.save("out/franzi/ear-lines-view.png")
    print("wrote out/franzi/ear-lines-view.png", sheet.size)


def emit():
    def pt(p):
        return f"[{p[0]:.4f}, {p[1]:.4f}]"

    rows = {"r": [], "l": []}
    for name, (ear, pts) in LINES.items():
        out, _, _ = snap(pts)
        rad = [((x - OX) / S, (y - OY) / S) for x, y in out]
        st, sg = tl.fit_chain(rad, tl.simplify(rad, 0.004))
        rows[ear].append(f"[{pt(st)}, [{', '.join(f'[{pt(c)}, {pt(e)}]' for c, e in sg)}]]")
    text = (
        "// Generated by harness/franzi_hair/ear_lines.py from ref/franzi/ 04. Do not edit by hand.\n"
        "// Open fold lines inside the ears, in head radii from the head centre (the calibration in harness/franzi_hair/trace.py).\n\n"
        'import type { Chain } from "./tables.ts";\n\n'
        + "".join(
            f"/** The fold lines of the {side} ear, each snapped onto the drawn dark line. */\nexport const ADULT_EAR_FOLDS_{key.upper()}: readonly Chain[] = [\n  " + ",\n  ".join(rows[key]) + ",\n];\n\n"
            for key, side in (("l", "left"), ("r", "right"))
        )
    )
    Path("ts/src/body-adult-ear-data.ts").write_text(text)
    print("wrote ts/src/body-adult-ear-data.ts")


if __name__ == "__main__":
    if sys.argv[1] == "view":
        view(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 12)
    else:
        emit()
