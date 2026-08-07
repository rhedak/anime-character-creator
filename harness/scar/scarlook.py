"""Crop the three heads to the same box and lay them out, so the scar can be
compared between the two characters and the two builds at a size it is legible
at. The scar is two thin strokes at 0.6 opacity, which at full-figure zoom is
about four pixels of ink.

The crop box comes from the skeleton rather than a fraction of the canvas: a
chibi head fills a different share of the figure than an adult's, so any fixed
fraction either cuts the chin off one or buries the other in torso.

It used to read three PNGs rendered separately by `render.sh` into a scratch
directory. It renders them itself now, so it survives a cleanup of `out/`.
"""

from __future__ import annotations

from pathlib import Path

import cairosvg
from PIL import Image

from anime_character_creator import BUILDS, PRESETS, build_skeleton, render_character

# Output goes to the ignored `out/`, not beside this file: the script now lives
# in the tracked tree and must not drop renders into it.
OUT = Path(__file__).resolve().parents[2] / "out" / "scar"
SHOTS = [
    ("satoko_scar", "satoko", "chibi"),
    ("satoshi_scar", "satoshi", "chibi"),
    ("satoshi_scar_real", "satoshi", "realistic"),
]


def head(name: str, preset: str, build: str) -> Image.Image:
    p = PRESETS[preset]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    png = OUT / f"{name}.png"
    cairosvg.svg2png(bytestring=render_character(p, sk).encode(), write_to=str(png), output_width=800)
    im = Image.open(png).convert("RGBA")
    # The PNG is exported at twice the SVG canvas, so skeleton coordinates have
    # to be doubled before they mean anything in this image.
    k2 = im.width / 400
    # A box a little wider than the skull, and down to just under the chin.
    pad = sk.head_r * 0.35
    box = (
        int((sk.head_cx - sk.head_r - pad) * k2),
        int((sk.head_cy - sk.head_r - pad) * k2),
        int((sk.head_cx + sk.head_r + pad) * k2),
        int((sk.head_cy + sk.head_r + pad) * k2),
    )
    crop = im.crop(box)
    # Same height for all three, so the scar is compared at one size.
    k = 420 / crop.height
    return crop.resize((round(crop.width * k), 420), Image.LANCZOS)


crops = [head(*s) for s in SHOTS]
pad = 16
w = sum(c.width for c in crops) + pad * (len(crops) + 1)
h = max(c.height for c in crops) + pad * 2
sheet = Image.new("RGBA", (w, h), (255, 255, 255, 255))
x = pad
for c in crops:
    sheet.paste(c, (x, pad), c)
    x += c.width + pad
sheet.save(OUT / "scarlook.png")
print("wrote", OUT / "scarlook.png", sheet.size)
