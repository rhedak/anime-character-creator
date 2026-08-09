"""Sideburn candidates, after the strip was made to track the face.

The shape question is settled by then: both edges ride `_head_edge_x` and the
taper runs the right way round. What is left is how far out the outer edge sits.
`_BEARD_SIDE_INSET` was tuned at 0.87 when there were no sideburns at all and
the mass had to be kept off the cheek by width alone; now the top edge's dive
does that job, and 0.87 leaves a band of skin between the strip and the head's
outline, which reads as a chinstrap sitting on the face rather than hair growing
out of it.

Judged at head size and tile size together, since the beard's whole history in
this repo is failing in opposite directions at the two.
"""

import io
import pathlib
import sys

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from anime_character_creator import PRESETS, build_skeleton, render_character
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/sideburn")
OUT.mkdir(parents=True, exist_ok=True)

NEW = C._beard


def _beard_before(sk, p):
    """The two-quadratic sideburn, kept here so the change can be judged as one.

    A verbatim copy of what `_beard` drew before 2026-08-09, comments stripped.
    Both edges are a single quadratic from the top of the strip to the bottom,
    which is the thing being replaced: a quadratic can be told where to bulge but
    not made to agree with the skull, so both edges came out as straight
    diagonals and the strip between them as a triangle.
    """
    if p.beard_color is None:
        return ""
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    b = sk.build
    sw = C._stroke_w(sk)
    top = C._BEARD_TOP
    drop = max(0.0, p.beard_length)
    chin = C._head_pt(180.0, 1.0, b)[1]
    x_top = C._head_edge_x(top, b) * C._BEARD_SIDE_INSET
    x_wide = C._head_edge_x(min(0.98, chin - 0.06), b) + drop * 1.25
    mid_y = chin + drop * 0.45
    bottom = chin + drop
    burn_y = C._BEARD_SIDEBURN_Y
    x_burn_out = C._head_edge_x(burn_y, b) * 0.99
    x_burn_in = x_burn_out * 0.70
    d = (
        f"M {cx - x_burn_out * r:.1f} {cy + burn_y * r:.1f} "
        f"Q {cx - x_top * r * 1.06:.1f} {cy + (burn_y + (top - burn_y) * 0.6) * r:.1f} "
        f"{cx - x_top * r:.1f} {cy + top * r:.1f} "
        f"Q {cx - x_wide * r:.1f} {cy + (top + (mid_y - top) * 0.55) * r:.1f} "
        f"{cx - x_wide * r:.1f} {cy + mid_y * r:.1f} "
        f"Q {cx - x_wide * r * 0.90:.1f} {cy + bottom * r:.1f} {cx:.1f} {cy + bottom * r:.1f} "
        f"Q {cx + x_wide * r * 0.90:.1f} {cy + bottom * r:.1f} "
        f"{cx + x_wide * r:.1f} {cy + mid_y * r:.1f} "
        f"Q {cx + x_wide * r:.1f} {cy + (top + (mid_y - top) * 0.55) * r:.1f} "
        f"{cx + x_top * r:.1f} {cy + top * r:.1f} "
        f"Q {cx + x_top * r * 1.06:.1f} {cy + (burn_y + (top - burn_y) * 0.6) * r:.1f} "
        f"{cx + x_burn_out * r:.1f} {cy + burn_y * r:.1f} "
        f"L {cx + x_burn_in * r:.1f} {cy + burn_y * r:.1f} "
        f"Q {cx + x_burn_in * r * 1.04:.1f} {cy + (burn_y + (top - burn_y) * 0.7) * r:.1f} "
        f"{cx + x_top * r * 0.74:.1f} {cy + (top + 0.14) * r:.1f} "
        f"Q {cx:.1f} {cy + 1.02 * r:.1f} {cx - x_top * r * 0.74:.1f} {cy + (top + 0.14) * r:.1f} "
        f"Q {cx - x_burn_in * r * 1.04:.1f} {cy + (burn_y + (top - burn_y) * 0.7) * r:.1f} "
        f"{cx - x_burn_in * r:.1f} {cy + burn_y * r:.1f} "
        f"Z"
    )
    return f'<path d="{d}" fill="{p.beard_color}" stroke="{C.OUTLINE}" stroke-width="{sw:.1f}" />'


# (label, outer ratio at `top`, width at the top of the strip, width at the join)
CANDIDATES = [
    ("before", 0.87, 0.11, 0.17),
    ("in .87", 0.87, 0.08, 0.17),
    ("shipped .93", 0.93, 0.08, 0.17),
    ("edge .98", 0.98, 0.08, 0.17),
]


def render(who, cand, size):
    label, inset, wtop, wbot = cand
    C._beard = _beard_before if label == "before" else NEW
    C._BEARD_SIDE_INSET = inset
    C._BEARD_SIDEBURN_W_TOP = wtop
    C._BEARD_SIDEBURN_W_BOT = wbot
    p = PRESETS[who]
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=800)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    if size == "head":
        w, h = im.size
        im = im.crop((int(w * 0.16), int(h * 0.04), int(w * 0.84), int(h * 0.62)))
        return im.resize((330, int(330 * im.height / im.width)), Image.LANCZOS)
    im.thumbnail((110, 145), Image.LANCZOS)
    return im


rows = []
for who in ("reinhard", "daizen"):
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
canv.save(OUT / "sideburn.png")
print("wrote", OUT / "sideburn.png", canv.size)
