"""Lid thickness, ours (eyes alone on skin) against the reference, per column, in reference pixels.

    ./harness/run.sh harness/franzi/lid_thickness.py

The black run directly above the iris/white in each column inside the eye's span: its top row, bottom row and thickness.
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image

subprocess.run(["node", "harness/franzi/lid_thickness.ts", "out/franzi/eyes-only.svg"], check=True)
subprocess.run(["node", "harness/franzi/underwear.ts", "adult_female", "out/franzi/al-meta.svg"], check=True)
meta = json.load(open("out/franzi/al-meta.json"))
sc = 352.0 / (2 * meta["head_r"])
subprocess.run([sys.executable, "harness/svg2png.py", "out/franzi/eyes-only.svg", "out/franzi/eyes-only.png", "--scale", str(sc)], check=True)
ours = np.array(Image.open("out/franzi/eyes-only.png").convert("RGBA")).astype(int)
ref = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")).astype(int)
CX_REF, CHIN_REF = 668.2, 434.0


def black(a):
    return (a[..., :3].mean(2) < 70) & (a[..., 3] > 128)


def run_at(mask, x, y0, y1):
    col = np.nonzero(mask[y0:y1, x])[0]
    if not len(col):
        return None
    s = col[0]
    e = s
    while e + 1 < len(col) and col[e + 1] == col[e] + 1:
        e += 1
    return y0 + int(col[s if False else 0]), y0 + int(col[e if False else min(e, len(col) - 1)])


bo, br = black(ours), black(ref)
# our canvas -> reference px: x_ref = CX_REF + (x_c - cx_c) * sc ; the ours png is at scale sc, so its column x_p = x_c * sc
cx_png = meta["canvas_w"] / 2 * sc
chin_png = meta["chin_y"] * sc
for name, xs in (("L (viewer's left)", range(558, 625, 6)), ("R (viewer's right)", range(698, 765, 6))):
    print(name, "  col | ref top-bottom (thick) | ours top-bottom (thick)")
    for xr in xs:
        yr0, yr1 = (255, 345) if name[0] == "R" else (270, 350)
        rr = run_at(br, xr, 285 if name[0] == "R" else 288, yr1)
        xp = int(round(cx_png + (xr - CX_REF)))
        oo = run_at(bo, xp, int(chin_png + (285 - CHIN_REF)), int(chin_png + (yr1 - CHIN_REF)))
        fm = lambda r, off: f"{r[0] - off:.0f}-{r[1] - off:.0f} ({r[1] - r[0] + 1})" if r else "none"
        print(f"   {xr}   {fm(rr, 0):22s} {fm(oo, int(chin_png - CHIN_REF)):22s}")
