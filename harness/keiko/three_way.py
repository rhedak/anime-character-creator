"""Reference, before and after, the same head-radius window each.

`before` is `ref-out/keiko.png` as it stood at `07617fb`, the commit this
campaign started from, read straight out of git rather than re-rendered: the
code that drew it is gone. That is safe to crop with today's skeleton because
this campaign changed only her clothes, and `skeleton_for` reads the body, the
hair margin and the hat, none of which moved. Both snapshots are the 400x500
canvas at scale 2, so the head sits at twice the skeleton's own coordinates.

Two rows: the whole figure, then the coat's front, where the milestones landed.
Composited onto white, never left on the reference's black page, which hides
every gap between a garment and our narrower hair.

Writes `out/keiko/three_way.png`.
"""

import io
import subprocess

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

BASE = "ref-local/keiko-tall-chibi"
OX, OY, R = 625.5, 394.0, 177.5  # the reference's, from `landmarks.py`
BEFORE_AT = "07617fb"
WHOLE = (-1.6, -1.2, 1.6, 5.4)
FRONT = (-1.15, 0.45, 1.15, 3.1)
ROW_H = 760


def on_white(im):
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3] if im.mode == "RGBA" else None)
    return bg


def reference():
    return on_white(Image.open(f"{BASE}/keiko-tall-chibi.png").convert("RGBA")), OX, OY, R


def snapshot(blob):
    im = on_white(Image.open(io.BytesIO(blob)).convert("RGBA"))
    sk = c.skeleton_for(PRESETS["keiko"])
    s = im.width / sk.canvas_w
    return im, sk.head_cx * s, sk.head_cy * s, sk.head_r * s


def before():
    return snapshot(subprocess.run(["git", "show", f"{BEFORE_AT}:ref-out/keiko.png"], capture_output=True, check=True).stdout)


def after():
    p = PRESETS["keiko"]
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    png = cairosvg.svg2png(bytestring=svg.encode(), scale=2)
    im = Image.open(io.BytesIO(png)).convert("RGB")
    return im, sk.head_cx * 2, sk.head_cy * 2, sk.head_r * 2


def window(src, box):
    im, cx, cy, r = src
    x0, y0, x1, y1 = box
    return im.crop((int(cx + x0 * r), int(cy + y0 * r), int(cx + x1 * r), int(cy + y1 * r)))


def row(box, label):
    names = ("reference", f"before ({BEFORE_AT})", "after")
    tiles = [window(src, box) for src in (reference(), before(), after())]
    tiles = [t.resize((int(t.width * ROW_H / t.height), ROW_H), Image.LANCZOS) for t in tiles]
    w = sum(t.width for t in tiles) + 40
    sheet = Image.new("RGB", (w, ROW_H + 26), (235, 235, 235))
    d = ImageDraw.Draw(sheet)
    x = 0
    for t, name in zip(tiles, names):
        sheet.paste(t, (x, 26))
        d.text((x + 6, 8), f"{name} ({label})", fill=(0, 0, 0))
        x += t.width + 20
    return sheet


def main():
    # The whole figure is tall and narrow and the coat front is wide, so the two
    # rows come out at very different natural widths. Scale each to one width
    # rather than padding the narrow one, which left half the sheet empty.
    rows = [row(WHOLE, "whole figure"), row(FRONT, "coat front")]
    w = max(r.width for r in rows)
    rows = [r.resize((w, int(r.height * w / r.width)), Image.LANCZOS) for r in rows]
    sheet = Image.new("RGB", (w, sum(r.height for r in rows) + 12), (235, 235, 235))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + 12
    sheet.save("out/keiko/three_way.png")
    print("out/keiko/three_way.png", sheet.size)


main()
