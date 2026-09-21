"""A bust sweep, to decide the range and the shape by looking.

No reference in this project measures a bust: Keiko's is a chibi and reads
close to flat, and `CLAUDE.md`'s direction is that references are not a target
for new work. So this is not a comparison, it is a sweep to judge against the
design intent (`docs/bust-plan.md`, B0).

Writes `out/bust/sweep.png`: each row one garment and build, each column a bust
value. On white and on black, because a silhouette change is exactly the kind
of thing a black page flatters.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

VALUES = (0.0, 0.25, 0.5, 0.75, 1.0)
TILE = 470
# A plain tunic, an open coat over a traced cut, and the same on the adult
# build, which is where the reach is widest.
ROWS = (
    ("satoko", "chibi", "#ffffff", "plain tunic"),
    ("satoko", "chibi", "#000000", "plain tunic, black"),
    ("keiko", "chibi", "#ffffff", "coat and traced cut"),
    ("satoko", "realistic", "#ffffff", "plain tunic, realistic"),
)


def render(preset: str, build: str, bg: str, bust: float) -> Image.Image:
    p = replace(PRESETS[preset], bust=bust)
    if build == "realistic":
        p = replace(p, body=None, heads=c.BUILDS["realistic"])
    sk = c.skeleton_for(p)
    png = cairosvg.svg2png(bytestring=c.render_character(p, sk, background=bg).encode(), scale=2)
    im = Image.open(io.BytesIO(png)).convert("RGB")
    # The torso only: the whole figure buries the change at this size.
    cx, cy, r = sk.head_cx * 2, sk.head_cy * 2, sk.head_r * 2
    return im.crop((int(cx - 1.6 * r), int(cy + 0.6 * r), int(cx + 1.6 * r), int(cy + 3.4 * r)))


def main() -> None:
    os.makedirs("out/bust", exist_ok=True)
    rows = []
    for preset, build, bg, label in ROWS:
        tiles = [render(preset, build, bg, v) for v in VALUES]
        tiles = [t.resize((int(t.width * TILE / t.height), TILE), Image.LANCZOS) for t in tiles]
        row = Image.new("RGB", (sum(t.width for t in tiles) + 40, TILE + 24), (235, 235, 235))
        d = ImageDraw.Draw(row)
        x = 0
        for t, v in zip(tiles, VALUES):
            row.paste(t, (x, 24))
            d.text((x + 6, 7), f"{label}  bust {v}", fill=(0, 0, 0))
            x += t.width + 10
        rows.append(row)
    w = max(r.width for r in rows)
    sheet = Image.new("RGB", (w, sum(r.height for r in rows) + 8 * len(rows)), (215, 215, 215))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + 8
    sheet.save("out/bust/sweep.png")
    print("out/bust/sweep.png", sheet.size)


main()
