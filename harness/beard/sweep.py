"""Beard candidates for Daizen and Reinhard, against their references.

The part is failing in both directions at once, so both are swept together: a
change that rescues one has to not ruin the other. Each candidate patches the
module's own constants rather than editing them, so the file on disk is never
half changed and the whole grid renders in one pass.

Judged at two sizes in the same sheet. The beard's whole problem is that it
either disappears or eats the face, and which of those it does depends on the
size you look at it.
"""

import io
import pathlib
import sys
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from anime_character_creator import PRESETS, build_skeleton, render_character
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/beard")
OUT.mkdir(parents=True, exist_ok=True)

# (label, top, x_top factor, length for daizen, length for reinhard, colour shift)
CANDIDATES = [
    ("now", 0.62, 1.00, 0.30, 0.12, 0.00),
    ("higher jaw", 0.70, 1.00, 0.30, 0.16, 0.00),
    ("inset sides", 0.62, 0.86, 0.34, 0.18, 0.00),
    ("both", 0.70, 0.88, 0.34, 0.20, 0.00),
]


def render(who, cand, size):
    _, top, xf, dz, rh, _shift = cand
    C._BEARD_TOP = top
    C._BEARD_SIDE_INSET = xf
    p = PRESETS[who]
    p = replace(p, beard_length=(dz if who == "daizen" else rh))
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=800)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    if size == "head":
        w, h = im.size
        im = im.crop((int(w * 0.14), int(h * 0.04), int(w * 0.86), int(h * 0.52)))
        return im.resize((300, int(300 * im.height / im.width)), Image.LANCZOS)
    im.thumbnail((110, 145), Image.LANCZOS)
    return im


rows = []
for who in ("daizen", "reinhard"):
    canon = Image.open(f"ref/{who}.png").convert("RGB")
    w, h = canon.size
    c = canon.crop((int(w * 0.28), int(h * 0.01), int(w * 0.72), int(h * 0.26)))
    tiles = [("canon", c.resize((300, int(300 * c.height / c.width)), Image.LANCZOS))]
    for cand in CANDIDATES:
        tiles.append((cand[0], render(who, cand, "head")))
        tiles.append(("", render(who, cand, "tile")))
    rows.append((who, tiles))

W = max(sum(t.width for _, t in ts) + 12 * (len(ts) + 1) for _, ts in rows)
H = sum(max(t.height for _, t in ts) + 40 for _, ts in rows) + 10
canv = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(canv)
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 17)
y = 6
for who, ts in rows:
    x = 12
    for label, t in ts:
        if label:
            d.text((x, y), f"{who[:3]} {label}", font=f, fill=(255, 255, 255))
        canv.paste(t, (x, y + 22))
        x += t.width + 12
    y += max(t.height for _, t in ts) + 40
canv.save(OUT / "beard.png")
print("wrote", OUT / "beard.png", canv.size)
