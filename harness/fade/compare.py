"""Where the two-tone hair boundary should sit, tried against the canon.

`_HAIR_FADE` is patched at runtime rather than edited, so the four candidates
render in one pass and the file on disk is never in a half-changed state.
"""

import io
import pathlib
import sys

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from anime_character_creator import PRESETS, build_skeleton, render_character
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/fade")
OUT.mkdir(parents=True, exist_ok=True)


def head(who, fade, crop_lift=None):
    C._HAIR_FADE = fade
    if crop_lift is not None:
        C._CROP_TONE_LIFT = crop_lift
    p = PRESETS[who]
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=800)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    w, h = im.size
    return im.crop((int(w * 0.10), int(h * 0.04), int(w * 0.90), int(h * 0.62)))


SWEEPS = {
    # Satoko's boundary is set by the clamp, so sweep the clamp.
    "satoko": [("fade %.2f" % f, dict(fade=f)) for f in (0.50, 0.62, 0.70, 0.78)],
    # Satoshi's fringe barely moved across the whole clamp sweep: his boundary is
    # set by how far the lift climbs each blade, not by the level line.
    "satoshi": [("lift %.2f" % v, dict(fade=0.50, crop_lift=v)) for v in (0.26, 0.20, 0.14, 0.09)],
}
rows = []
for who in ("satoko", "satoshi"):
    canon = Image.open(f"ref/{who}.png").convert("RGB")
    w, h = canon.size
    tiles = [("canon", canon.crop((int(w * 0.26), int(h * 0.02), int(w * 0.74), int(h * 0.46))))]
    for label, kw in SWEEPS[who]:
        tiles.append((label, head(who, **kw)))
    rows.append((who, [(l, t.resize((300, int(300 * t.height / t.width)), Image.LANCZOS)) for l, t in tiles]))

W = max(sum(t.width for _, t in ts) + 14 * (len(ts) + 1) for _, ts in rows)
H = sum(max(t.height for _, t in ts) + 40 for _, ts in rows) + 10
canv = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(canv)
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
y = 6
for who, ts in rows:
    x = 14
    for label, t in ts:
        d.text((x, y), f"{who} {label}", font=f, fill=(255, 255, 255))
        canv.paste(t, (x, y + 22))
        x += t.width + 14
    y += max(t.height for _, t in ts) + 40
canv.save(OUT / "fade.png")
print("wrote", OUT / "fade.png", canv.size)
