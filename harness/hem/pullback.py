"""How hard a requested hem length gets pulled back toward the skeleton's own
shorter hem at low builds.

`_skirt_hem_y` blends the requested length in by `sk.build`, which is 0.1 at
chibi, so two lengths as far apart as 0.60 and 0.95 land within four pixels of
each other: task #103's report, and the reason Reika's near-floor-length
reference hakama reads mid-thigh at the published build. The blend was a
deliberate choice against a real failure, a full-length skirt swallowing a
chibi's short legs and reading as a bell with no limbs underneath it, so this
sweeps candidates rather than just removing it.

Four characters whose hem is set at a real length, from short to long:
Satoko's skirt (0.70), Chiyo's (0.78), Haruto's hakama (0.60), Reika's (0.95).
The current behaviour is candidate zero, not removed, since a short hem at
chibi can be the right call even where it was not the original plan.
"""

import io
import pathlib
import sys

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from anime_character_creator import PRESETS, build_skeleton, render_character
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/hem")
OUT.mkdir(parents=True, exist_ok=True)

BASE = C._skirt_hem_y


def make_hem(blend):
    def _skirt_hem_y(sk, length):
        if length is None:
            return sk.hem_y
        asked = sk.hip_y + length * (sk.ankle_y - sk.hip_y)
        return sk.hem_y + (asked - sk.hem_y) * blend(sk.build)

    return _skirt_hem_y


# (label, blend(build) -> 0..1)
CANDIDATES = [
    ("current", lambda b: b),
    ("sqrt", lambda b: b**0.5),
    ("floor .35", lambda b: max(b, 0.35)),
    ("floor .5", lambda b: max(b, 0.5)),
    ("full", lambda b: 1.0),
]


def render(preset, cand, size):
    _, blend = cand
    C._skirt_hem_y = make_hem(blend)
    p = PRESETS[preset]
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=800)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    w, h = im.size
    if size == "body":
        im = im.crop((int(w * 0.16), int(h * 0.28), int(w * 0.84), int(h * 1.00)))
        return im.resize((240, int(240 * im.height / im.width)), Image.LANCZOS)
    im.thumbnail((100, 135), Image.LANCZOS)
    return im


rows = []
for preset in ("satoko", "chiyo", "haruto", "reika"):
    canon = Image.open(f"ref/{preset}.png").convert("RGB")
    w, h = canon.size
    c = canon.crop((int(w * 0.10), int(h * 0.30), int(w * 0.90), int(h * 0.95)))
    tiles = [("canon", c.resize((240, int(240 * c.height / c.width)), Image.LANCZOS))]
    for cand in CANDIDATES:
        tiles.append((cand[0], render(preset, cand, "body")))
        tiles.append(("", render(preset, cand, "tile")))
    rows.append((preset, tiles))
C._skirt_hem_y = BASE

W = max(sum(t.width for _, t in ts) + 10 * (len(ts) + 1) for _, ts in rows)
H = sum(max(t.height for _, t in ts) + 34 for _, ts in rows) + 10
canv = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(canv)
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
y = 6
for preset, ts in rows:
    x = 10
    for label, t in ts:
        if label:
            d.text((x, y), f"{preset[:3]} {label}", font=f, fill=(255, 255, 255))
        canv.paste(t, (x, y + 22))
        x += t.width + 10
    y += max(t.height for _, t in ts) + 34
canv.save(OUT / "pullback.png")
print("wrote", OUT / "pullback.png", canv.size)
