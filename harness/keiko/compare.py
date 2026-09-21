"""Keiko beside her reference, the same head-radius window each.

Each side is cropped to the same box in its own head radii (the reference by
`landmarks.py`'s calibration, ours by the skeleton), so "do the clothes hang
the same" is answered directly rather than by eyeballing two figures at two
scales. Writes `out/keiko/compare.png`: the whole figure each side, then the
coat's front at 2x, which is where this campaign's milestones land.

The reference is composited onto white, not left on its black page: a black
background hides every gap between a garment and our narrower hair, which is
the mistake the witch-hat pass made twice.
"""

import io
import os

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

BASE = "ref-local/keiko-tall-chibi"
# From `landmarks.py`, which re-derives these and prints them.
OX, OY, R = 625.5, 394.0, 177.5

WHOLE = (-1.6, -1.2, 1.6, 5.4)
FRONT = (-1.1, 0.5, 1.1, 3.2)


def ours(scale=2):
    p = PRESETS["keiko"]
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB")
    return im, sk.head_cx * scale, sk.head_cy * scale, sk.head_r * scale


def ref():
    im = Image.open(f"{BASE}/keiko-tall-chibi.png").convert("RGBA")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    return bg, OX, OY, R


def window(im, cx, cy, r, box):
    x0, y0, x1, y1 = box
    return im.crop((int(cx + x0 * r), int(cy + y0 * r), int(cx + x1 * r), int(cy + y1 * r)))


def strip(box, height, label):
    tiles = [window(*src, box) for src in (ref(), ours())]
    tiles = [t.resize((int(t.width * height / t.height), height), Image.LANCZOS) for t in tiles]
    w = sum(t.width for t in tiles) + 30
    sheet = Image.new("RGB", (w, height + 24), (230, 230, 230))
    x = 0
    for t, name in zip(tiles, ("reference", "ours")):
        sheet.paste(t, (x, 24))
        ImageDraw.Draw(sheet).text((x + 6, 6), f"{name} ({label})", fill=(0, 0, 0))
        x += t.width + 30
    return sheet


def main():
    os.makedirs("out/keiko", exist_ok=True)
    a = strip(WHOLE, 900, "whole figure")
    b = strip(FRONT, 900, "coat front, 2x")
    sheet = Image.new("RGB", (a.width + b.width + 40, max(a.height, b.height)), (230, 230, 230))
    sheet.paste(a, (0, 0))
    sheet.paste(b, (a.width + 40, 0))
    sheet.save("out/keiko/compare.png")
    print("out/keiko/compare.png", sheet.size)


main()
