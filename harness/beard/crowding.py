"""Where the beard, the hair and the ear all arrive at once.

The strip's top is at 0.02 head radii and its outer edge at 0.99 of the skull's,
which is the head's widest point, where the side hair comes down and one
hundredth above where the ear attaches. Three outlines meet there and butt into
each other rather than one tucking under another.

Two families of answer, swept together because they are alternatives and the
cheap one should win if it can:

- **Geometry.** Arrive thinner. `w_top` narrows the strip where it meets the
  hair, `ease` holds it thin further down instead of opening evenly the whole
  way, and `out` pulls the outer edge in off the skull's own edge so the strip
  runs behind the ear's attach line rather than on it.
- **Z-order.** Draw the thing it collides with on top of it. The owner's
  suggestion, and worth rendering even where it is known to cost something
  elsewhere, because seeing it is how you find out whether it was worth paying.

The z-order candidates are patched rather than reordered: `_glasses` is drawn
immediately after the beard, so appending a part to it and blanking that part's
own slot moves it over the beard exactly and changes nothing else.

Judged at head size and tile size together. Thinner is the direction of this
part's standing failure, which is vanishing when the figure is shrunk.
"""

import io
import pathlib
import sys

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from anime_character_creator import PRESETS, build_skeleton, render_character
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/crowding")
OUT.mkdir(parents=True, exist_ok=True)

EARS, MASS, GLASSES = C._ears, C._hair_mass, C._glasses

# (label, w_top, ease, outer ratio at the top of the strip, what to lift over it)
CANDIDATES = [
    ("now", 0.08, 1.0, 0.99, None),
    ("w .05", 0.05, 1.0, 0.99, None),
    ("w .04 ease2", 0.04, 2.0, 0.99, None),
    ("w .04 ease2 out .94", 0.04, 2.0, 0.94, None),
    ("z ears over", 0.08, 1.0, 0.99, "ears"),
    ("z hair over", 0.08, 1.0, 0.99, "hair"),
    ("thin + z both", 0.04, 2.0, 0.94, "both"),
]


def zorder(lift):
    """Put `lift` over the beard by hanging it off the part drawn next after it."""
    C._ears, C._hair_mass, C._glasses = EARS, MASS, GLASSES
    over = []
    if lift in ("ears", "both"):
        C._ears = lambda sk, p: ""
        over.append(EARS)
    if lift in ("hair", "both"):
        C._hair_mass = lambda sk, p: ""
        over.append(MASS)
    if over:
        C._glasses = lambda sk, p: "\n  ".join([GLASSES(sk, p), *(f(sk, p) for f in over)])


def render(who, cand, size):
    _, wtop, ease, out, lift = cand
    C._BEARD_SIDEBURN_W_TOP = wtop
    C._BEARD_SIDEBURN_W_EASE = ease
    C._BEARD_SIDEBURN_OUT = out
    zorder(lift)
    p = PRESETS[who]
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=800)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    if size == "head":
        w, h = im.size
        im = im.crop((int(w * 0.16), int(h * 0.04), int(w * 0.84), int(h * 0.50)))
        return im.resize((300, int(300 * im.height / im.width)), Image.LANCZOS)
    im.thumbnail((105, 140), Image.LANCZOS)
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

W = max(sum(t.width for _, t in ts) + 10 * (len(ts) + 1) for _, ts in rows)
H = sum(max(t.height for _, t in ts) + 40 for _, ts in rows) + 10
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
    y += max(t.height for _, t in ts) + 40
canv.save(OUT / "crowding.png")
print("wrote", OUT / "crowding.png", canv.size)
