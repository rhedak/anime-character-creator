"""Satoshi with the katana beside the reference, same head-radius window each.

Each side is cropped to the same box in its own head radii (the reference by its
calibration, ours by the skeleton), so "does it hang right" is answered directly.
Writes `out/katana/compare.png`: the whole figure, then the hip window at 2x, then
the same window at 4x on our render alone.
"""

import io
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

BASE = "ref-local/satoshi-tall-chibi-katana"
OX, OY, R = 626.0, 308.0, 171.5
SAYA = "#3c322b"


def ours(scale):
    p = PRESETS["satoshi"]
    p = replace(p, outfit=replace(p.outfit, katana_color=SAYA))
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB")
    return im, sk


def window(im, cx, cy, r, box):
    x0, y0, x1, y1 = box
    return im.crop((int(cx + x0 * r), int(cy + y0 * r), int(cx + x1 * r), int(cy + y1 * r)))


def main():
    ref = Image.open(f"{BASE}/satoshi-tall-chibi-sword.png").convert("RGBA")
    bg = Image.new("RGB", ref.size, (255, 255, 255))
    bg.paste(ref, mask=ref.split()[3])
    K = 2
    im, sk = ours(K)
    box = (-1.3, 0.2, 2.2, 6.0)
    a = window(bg, OX, OY, R, box)
    b = window(im, sk.head_cx * K, sk.head_cy * K, sk.head_r * K, box)
    H = 900
    a, b = (t.resize((int(t.width * H / t.height), H), Image.LANCZOS) for t in (a, b))
    sheet = Image.new("RGB", (a.width + b.width + 30, H + 24), (230, 230, 230))
    sheet.paste(a, (0, 24))
    sheet.paste(b, (a.width + 30, 24))
    d = ImageDraw.Draw(sheet)
    d.text((6, 6), "reference", fill=(0, 0, 0))
    d.text((a.width + 36, 6), "ours (same head-radius window)", fill=(0, 0, 0))
    sheet.save("out/katana/compare.png")
    print(sheet.size)


main()
