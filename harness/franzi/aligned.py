"""Side-by-side crops of the reference and our render, aligned by the body gate's mapping (chin row, sole row, centre line).

    ./harness/run.sh harness/franzi/aligned.py NAME x0 y0 x1 y1 [OVERRIDES_JSON]

REF=02-blouse (or any file of ref/franzi/ without .png) compares against that reference instead of ref 04, for the outfits.

The box (x0, y0, x1, y1) is in reference canvas pixels (ref 04, 1312 x 2440). Our figure is rendered at the scale that makes a head
height equal to the reference's 352 px, and cropped to the same box through the mapping, so the shoulders, the bust and the hem
line up. Writes out/franzi/aligned-NAME.png (reference left, ours right). Replaces the earlier hand-placed crops, which were
about 0.3 head heights out vertically.
"""

import json
import subprocess
import sys

from PIL import Image

name, x0, y0, x1, y1 = sys.argv[1], *map(int, sys.argv[2:6])
over = sys.argv[6] if len(sys.argv) > 6 else "{}"
subprocess.run(["node", "harness/franzi/franzi.ts", "out/franzi/franzi.svg", over], check=True)
subprocess.run(["node", "harness/franzi/underwear.ts", "adult_female", "out/franzi/al-meta.svg"], check=True)
meta = json.load(open("out/franzi/al-meta.json"))
H_REF, CX_REF, CHIN_REF = 352.0, 668.2, 434.0
r = meta["head_r"]
scale = H_REF / (2 * r)  # render px per canvas unit so that a head height (2 radii) is 352 px
subprocess.run([sys.executable, "harness/svg2png.py", "out/franzi/franzi.svg", "out/franzi/franzi.png", "--scale", f"{scale:.5f}"], check=True)


def flat(p):
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    return bg.convert("RGB")


import os

ref = flat(f"ref/franzi/{os.environ.get('REF', '04-bikini-fullbody')}.png").crop((x0, y0, x1, y1))
ours_cx = (meta["canvas_w"] / 2) * scale
ours_chin = meta["chin_y"] * scale
ox0, oy0 = ours_cx + (x0 - CX_REF), ours_chin + (y0 - CHIN_REF)
ren = flat("out/franzi/franzi.png").crop((round(ox0), round(oy0), round(ox0) + (x1 - x0), round(oy0) + (y1 - y0)))
w, h = ref.size
im = Image.new("RGB", (2 * w + 20, h), "white")
im.paste(ref, (0, 0))
im.paste(ren, (w + 20, 0))
import os

zoom = float(os.environ.get("ZOOM", "1"))
if zoom != 1:
    im = im.resize((round(im.width * zoom), round(im.height * zoom)), Image.LANCZOS)
im.save(f"out/franzi/aligned-{name}.png")
# 50% overlay of ours on the reference, same alignment
ov = Image.blend(ref, ren, 0.5)
if zoom != 1:
    ov = ov.resize((round(ov.width * zoom), round(ov.height * zoom)), Image.LANCZOS)
ov.save(f"out/franzi/overlay-{name}.png")
print("wrote", f"out/franzi/aligned-{name}.png", "scale", round(scale, 4))
