"""How high and how wide the moustache lobe goes.

The beard used to sit entirely below the chin, which read as a shaved face on an
unshaved neck. Bringing the coverage up over the mouth is the owner's call; the
question this answers is how far, and the two numbers pull against each other.

Too low or too narrow and nothing changed, the mass is still a bib under the
jaw. Too high or too wide and the lobe stops being a moustache and becomes the
surgical mask this part drew on its first attempt, which is the failure the old
diving top edge existed to avoid. The first try at 0.42 by 0.30 was well into
that: a rounded blob from under the eyes down, reading as something worn.

The mouth is drawn over the beard now rather than under it, so it is in every
tile here; whether it survives against a dark beard is part of what is being
judged, not a detail. Tile size included for the usual reason.
"""

import io
import pathlib
import sys

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from anime_character_creator import PRESETS, build_skeleton, render_character
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/moustache")
OUT.mkdir(parents=True, exist_ok=True)

# (label, top of the lobe, its half width), both in head radii. The mouth sits at
# 0.55 and the chin at 1.0, so a lobe top above about 0.40 is level with the nose.
CANDIDATES = [
    ("y.46 SHIPPED", 0.46, 0.24, 2.3),
    ("y.41 w.24", 0.41, 0.24, 2.3),
    ("y.36 w.24", 0.36, 0.24, 2.3),
    ("y.36 w.28", 0.36, 0.28, 2.3),
    ("y.31 w.28", 0.31, 0.28, 2.3),
    ("y.36 w.28 lip1.9", 0.36, 0.28, 1.9),
]


def render(who, cand, size):
    _, ty, th, lip = cand
    C._BEARD_TASH_Y, C._BEARD_TASH_HALF, C._BEARD_LIP_W = ty, th, lip
    p = PRESETS[who]
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=800)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    if size == "head":
        w, h = im.size
        im = im.crop((int(w * 0.18), int(h * 0.04), int(w * 0.82), int(h * 0.52)))
        return im.resize((280, int(280 * im.height / im.width)), Image.LANCZOS)
    im.thumbnail((100, 135), Image.LANCZOS)
    return im


rows = []
for who in ("reinhard", "daizen"):
    canon = Image.open(f"ref/{who}.png").convert("RGB")
    w, h = canon.size
    c = canon.crop((int(w * 0.28), int(h * 0.01), int(w * 0.72), int(h * 0.26)))
    tiles = [("canon", c.resize((280, int(280 * c.height / c.width)), Image.LANCZOS))]
    for cand in CANDIDATES:
        tiles.append((cand[0], render(who, cand, "head")))
        tiles.append(("", render(who, cand, "tile")))
    rows.append((who, tiles))

W = max(sum(t.width for _, t in ts) + 10 * (len(ts) + 1) for _, ts in rows)
H = sum(max(t.height for _, t in ts) + 38 for _, ts in rows) + 10
canv = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(canv)
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
y = 6
for who, ts in rows:
    x = 10
    for label, t in ts:
        if label:
            d.text((x, y), f"{who[:3]} {label}", font=f, fill=(255, 255, 255))
        canv.paste(t, (x, y + 22))
        x += t.width + 10
    y += max(t.height for _, t in ts) + 38
canv.save(OUT / "moustache.png")
print("wrote", OUT / "moustache.png", canv.size)
