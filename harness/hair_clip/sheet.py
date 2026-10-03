"""Deferred item, a hair clip for Katherina where her side tail's band was (the
owner, 2026-10-03). The first version of this script drew five candidate
shapes over a render in gold, her collar's colour (the owner's pick); the owner
kept all five as `HAIR_CLIPS`, picked in the web tool, so it now draws the
generator's own clip.

Two sheets, in `out/hair_clip/`:

- `sheet.png`: each shape on Katherina, with the hat, without it, and at the
  insert size (head radius 21 px) at 1x, enlarged 3x so its pixels show.
- `cuts.png`: the crescent and the bar on every hairstyle without a hat, to
  check the spot lands on hair whatever the cut.

    ./harness/run.sh harness/hair_clip/sheet.py
"""

import io
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_clip"
GOLD = "#c4903c"


def clipped(p, shape):
    return replace(p, outfit=replace(p.outfit, hair_clip_color=GOLD, hair_clip=shape))


def no_hat(p):
    return replace(p, outfit=replace(p.outfit, hat_color=None, hat_band_color=None))


def render(p, scale, box):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="white")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB")
    cx, cy, r = sk.head_cx * scale, sk.head_cy * scale, sk.head_r * scale
    x0, y0, x1, y1 = box
    return im.crop((round(cx + x0 * r), round(cy + y0 * r), round(cx + x1 * r), round(cy + y1 * r)))


def sheet(rows, path):
    W = max(sum(t.width + 8 for t in row) for _, row in rows)
    H = sum(max(t.height for t in row) + 24 for _, row in rows)
    out = Image.new("RGB", (W, H), (150, 150, 150))
    d = ImageDraw.Draw(out)
    y = 0
    for name, row in rows:
        d.text((4, y + 6), name, fill=(0, 0, 0))
        x = 0
        for t in row:
            out.paste(t, (x, y + 22))
            x += t.width + 8
        y += max(t.height for t in row) + 24
    out.save(path)
    print(path, out.size)


def main() -> None:
    kat = replace(PRESETS["katherina"], familiar_color=None)
    small = 21 / c.skeleton_for(kat).head_r
    head = (-1.6, -1.3, 1.6, 1.1)
    rows = []
    for shape in c.HAIR_CLIPS:
        tiny = render(clipped(kat, shape), small, (-2.0, -2.2, 2.0, 2.6))
        row = [
            render(clipped(kat, shape), 2.0, head),
            render(clipped(no_hat(kat), shape), 2.0, head),
            tiny.resize((tiny.width * 3, tiny.height * 3), Image.NEAREST),
        ]
        rows.append((f"{shape}: hat, no hat, insert size (21 px head radius) at 3x", row))
    sheet(rows, f"{OUT}/sheet.png")

    rows = []
    for shape in ("crescent", "bar"):
        row = []
        for cut in sorted(c.HAIRSTYLES):
            row.append(render(clipped(replace(no_hat(kat), hairstyle=cut), shape), 1.2, head))
        rows.append((f"{shape} on " + ", ".join(sorted(c.HAIRSTYLES)), row))
    sheet(rows, f"{OUT}/cuts.png")


if __name__ == "__main__":
    main()
