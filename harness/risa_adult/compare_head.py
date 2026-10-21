"""Franzi's render over Risa's bikini reference, at the head, to see what her traced head already gets right.

    ./harness/run.sh harness/risa_adult/compare_head.py [x0 y0 x1 y1] [REFFILE]

Needs out/franzi/franzi.svg (node harness/franzi/franzi.ts) and out/franzi/al-meta.json (harness/franzi/underwear.ts), the same
inputs harness/franzi/aligned.py uses. Risa's images are on Franzi's 1312 px grid with the head where Franzi's is (ref/risa-adult/README.md),
so the mapping is aligned.py's: a head height of 352 px, the centre line at 668.2 and the chin at 434.
Writes out/risa_adult/head-compare.png: reference left, ours middle, a 50% blend right.
"""

import json
import os
import subprocess
import sys

from PIL import Image

args = sys.argv[1:]
box = tuple(int(a) for a in args[:4]) if len(args) >= 4 else (400, 40, 940, 560)
ref_path = args[4] if len(args) > 4 else "ref/risa-adult/00-bikini.png"
meta = json.load(open("out/franzi/al-meta.json"))
H_REF, CX_REF, CHIN_REF = 352.0, 668.2, 434.0
scale = H_REF / (2 * meta["head_r"])
SVG = os.environ.get("SVG", "out/franzi/franzi.svg")
PNG = SVG[:-4] + ".png"
subprocess.run([sys.executable, "harness/svg2png.py", SVG, PNG, "--scale", f"{scale:.5f}"], check=True)


def flat(p):
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    return bg.convert("RGB")


x0, y0, x1, y1 = box
ref = flat(ref_path).crop(box)
ox0 = (meta["canvas_w"] / 2) * scale + (x0 - CX_REF)
oy0 = meta["chin_y"] * scale + (y0 - CHIN_REF)
ren = flat(PNG).crop((round(ox0), round(oy0), round(ox0) + (x1 - x0), round(oy0) + (y1 - y0)))
w, h = ref.size
im = Image.new("RGB", (3 * w + 40, h), "white")
im.paste(ref, (0, 0))
im.paste(ren, (w + 20, 0))
im.paste(Image.blend(ref, ren, 0.5), (2 * w + 40, 0))
zoom = float(os.environ.get("ZOOM", "1"))
if zoom != 1:
    im = im.resize((round(im.width * zoom), round(im.height * zoom)), Image.LANCZOS)
im.save("out/risa_adult/head-compare.png")
print("wrote out/risa_adult/head-compare.png", im.size)
