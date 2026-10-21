"""Three panels side by side on the reference's pixel grid: the reference, one render, another render.

    ./harness/run.sh harness/risa_adult/compare3.py BEFORE.svg AFTER.svg x0 y0 x1 y1 [ZOOM] [OUT.png]

The mapping is compare_head.py's (a head height of 352 px, the centre line at 668.2, the chin at 434). Writes out/risa_adult/compare3.png (or OUT).
"""

import json
import subprocess
import sys

from PIL import Image, ImageDraw

before, after = sys.argv[1], sys.argv[2]
box = tuple(int(v) for v in sys.argv[3:7])
zoom = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
out = sys.argv[8] if len(sys.argv) > 8 else "out/risa_adult/compare3.png"
meta = json.load(open("out/franzi/al-meta.json"))
H_REF, CX_REF, CHIN_REF = 352.0, 668.2, 434.0
scale = H_REF / (2 * meta["head_r"])


def flat(p):
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    return bg.convert("RGB")


def render(svg):
    png = svg[:-4] + ".png"
    subprocess.run([sys.executable, "harness/svg2png.py", svg, png, "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
    x0, y0, x1, y1 = box
    ox0 = (meta["canvas_w"] / 2) * scale + (x0 - CX_REF)
    oy0 = meta["chin_y"] * scale + (y0 - CHIN_REF)
    return flat(png).crop((round(ox0), round(oy0), round(ox0) + (x1 - x0), round(oy0) + (y1 - y0)))


import os

ref = flat(os.environ.get("REF", "ref/risa-adult/00-bikini.png")).crop(box)
panels = [("reference", ref), ("current", render(before)), ("traced", render(after))]
w, h = ref.size
pad = 22
sheet = Image.new("RGB", (3 * w + 2 * 16, h + pad), "white")
for i, (name, im) in enumerate(panels):
    sheet.paste(im, (i * (w + 16), pad))
    ImageDraw.Draw(sheet).text((i * (w + 16) + 4, 5), name, fill=(0, 0, 0))
if zoom != 1:
    sheet = sheet.resize((round(sheet.width * zoom), round(sheet.height * zoom)), Image.LANCZOS)
sheet.save(out)
print("wrote", out, sheet.size)
