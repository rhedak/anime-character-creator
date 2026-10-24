"""Stage 3 of docs/risa-polish-plan.md: Risa's uniform, piece by piece, on the traced body and on her slender build, beside the references.

    ./harness/run.sh harness/risa_adult/uniform_check.py

Renders the preset with and without the blazer, each on the traced body (`body_build` null) and on hers, maps them to the bikini's grid (compare_head.py's mapping) and writes
out/risa_adult/uniform-<region>.png for each region: the reference (01 with the blazer, 02 without, registered by the irises, registration.py), the traced body, the slender
build. The uniform references are drawn about 6% narrower than the bikini image and with shorter legs (the plan's decision 1: drift), so they are for the shapes of the
pieces and where they sit on the body, not for widths. Then counts the skin a garment should cover: skin-coloured pixels in the torso's rows (below the collar, above the
skirt's hem) outside the neck's V and the hands, for each render.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "harness/risa_adult")
from registration import Registration  # noqa: E402

OUT = Path("out/risa_adult")
OUT.mkdir(parents=True, exist_ok=True)
H, CX, CHIN = 352.0, 668.2, 434.0
W, HT = 1312, 2300
subprocess.run(["node", "harness/franzi/underwear.ts", "adult_female", "out/franzi/al-meta.svg"], check=True, stderr=subprocess.DEVNULL)
meta = json.load(open("out/franzi/al-meta.json"))
scale = H / (2 * meta["head_r"])


def render(name, overrides):
    svg = OUT / f"uc-{name}.svg"
    subprocess.run(["node", "harness/risa_adult/risa.ts", str(svg), json.dumps({"_preset": "risa", **overrides})], check=True, stderr=subprocess.DEVNULL)
    png = svg.with_suffix(".png")
    subprocess.run([sys.executable, "harness/svg2png.py", str(svg), str(png), "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
    im = Image.open(png).convert("RGBA")
    ox, oy = round((meta["canvas_w"] / 2) * scale - CX), round(meta["chin_y"] * scale - CHIN)
    return im.crop((ox, oy, ox + W, oy + HT))


def ref(name):
    return Registration(f"ref/risa-adult/{name}.png").register(Image.open(f"ref/risa-adult/{name}-transparent.png").convert("RGBA"), size=(W, HT))


def on_white(im):
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    return bg.convert("RGB")


def strip(panels, box, out, zoom):
    crops = [on_white(p).crop(box) for p in panels]
    w, h = crops[0].size
    s = Image.new("RGB", (w * len(crops) + 12 * (len(crops) - 1), h), "white")
    d = ImageDraw.Draw(s)
    for i, c in enumerate(crops):
        s.paste(c, (i * (w + 12), 0))
        for k in range(-2, 14):  # guide lines every half head height
            y = CHIN + k * H / 2 - box[1]
            if 0 <= y < h:
                d.line([(i * (w + 12), y), (i * (w + 12) + w, y)], fill=(0, 160, 255))
    s.resize((round(s.width * zoom), round(s.height * zoom)), Image.LANCZOS).save(out)


NO_BLAZER = {"outfit": {"coat_color": None}}
panels = {
    "blazer": [ref("01-school-uniform"), render("traced", {"body_build": None}), render("slender", {})],
    "shirt": [ref("02-uniform-no-blazer"), render("traced-shirt", {"body_build": None, **NO_BLAZER}), render("slender-shirt", NO_BLAZER)],
}
REGIONS = {  # bikini-grid boxes (x0, y0, x1, y1) and the zoom of the strip
    "collar": ((520, 420, 820, 720), 1.0),
    "torso": ((380, 500, 960, 1200), 0.6),
    "skirt": ((380, 980, 960, 1360), 0.7),
    "cuffs": ((300, 1020, 560, 1320), 1.0),
    "legs": ((420, 1300, 920, 2300), 0.45),
}
for kind, ps in panels.items():
    for region, (box, zoom) in REGIONS.items():
        strip(ps, box, OUT / f"uniform-{kind}-{region}.png", zoom)

# skin a garment should cover: in the rows from the collar's foot to just above the skirt's hem, skin-coloured pixels outside the V of the neck and the hands' columns
SKIN = np.array([0xFA, 0xC4, 0xA8])
for kind, ps in panels.items():
    for label, im in zip(("traced", "slender"), ps[1:]):
        a = np.array(im).astype(int)
        skin = (np.abs(a[..., :3] - SKIN).sum(2) < 30) & (a[..., 3] > 200)
        rows = slice(int(CHIN + 0.35 * H), int(CHIN + 2.05 * H))
        band = skin[rows]
        cols = np.zeros(W, bool)
        cols[int(CX - 0.3 * H) : int(CX + 0.3 * H)] = True  # the torso's middle, where no hand reaches
        print(f"{kind:6s} {label:8s} skin pixels under the garments, torso middle {int(band[:, cols].sum()):6d}, whole width {int(band.sum()):6d}")
