"""How far the beard hangs below the chin, and what shape its bottom is.

Two questions the owner put together on 2026-08-09, and they belong together
because the answer to one changes the answer to the other.

The hang is `beard_length`, which drives how far past the chin the mass reaches
and, through `x_wide`, how far wide of the jaw it swings. At the shipped values
it reads as a beard growing down the neck rather than one sitting on a jaw.

The bottom line is either the arc that has always been there, swinging wide and
squaring off under the chin, or the jaw's own line moved down by the length.
They say different things: the arc is a beard with bulk of its own, the jaw
track is growth of an even depth following the face. The second is the one that
should survive being made short, since a shallow arc is a crescent that could be
anything while a jaw line stays a jaw at any depth. Which is why the two are
swept as a grid rather than one after the other.
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

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/hang")
OUT.mkdir(parents=True, exist_ok=True)

JAW = C._jaw_track


def _arc(y0, build, drop, inset, steps=12):
    """The bottom as it was before 2026-08-09, as points on the same interface.

    An arc swung `drop * 1.25` wide of the jaw and squared off `drop` under the
    chin, owing its shape to nothing about the head. Sampled off the two
    quadratics it used to be drawn as, so the comparison is like for like.
    """
    chin = C._head_pt(180.0, 1.0, build)[1]
    x_top = C._head_edge_x(y0, build) * inset
    x_wide = C._head_edge_x(min(0.98, chin - 0.06), build) + drop * 1.25
    mid_y, bottom = chin + drop * 0.45, chin + drop
    legs = [
        ((x_top, y0), (x_wide, y0 + (mid_y - y0) * 0.55), (x_wide, mid_y)),
        ((x_wide, mid_y), (x_wide * 0.90, bottom), (0.0, bottom)),
    ]
    pts = []
    for (sx, sy), (kx, ky), (ex, ey) in legs:
        for i in range(1, steps + 1):
            t = i / steps
            u = 1 - t
            pts.append(
                (u * u * sx + 2 * u * t * kx + t * t * ex, u * u * sy + 2 * u * t * ky + t * t * ey)
            )
    return pts


# (label, which bottom, what to scale `beard_length` by). Scales are against the
# shipped presets, which were shortened by more than half when the shape changed,
# so x2.5 is roughly the old hang and x1 is what ships.
CANDIDATES = [
    ("arc x2.5", _arc, 2.50),
    ("arc x1", _arc, 1.00),
    ("jaw x2.5", JAW, 2.50),
    ("jaw x1.6", JAW, 1.60),
    ("jaw x1 SHIPPED", JAW, 1.00),
    ("jaw x0.6", JAW, 0.60),
]


def render(who, cand, size):
    _, bottom, scale = cand
    C._jaw_track = bottom
    p = PRESETS[who]
    p = replace(p, beard_length=p.beard_length * scale)
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=800)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    if size == "head":
        w, h = im.size
        im = im.crop((int(w * 0.18), int(h * 0.04), int(w * 0.82), int(h * 0.56)))
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
canv.save(OUT / "hang.png")
print("wrote", OUT / "hang.png", canv.size)
