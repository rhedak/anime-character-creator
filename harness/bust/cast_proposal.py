"""Step 7's proposal: a bust value per female character, and the overview to
judge it by (`docs/bust-plan.md`, step 7).

Best guesses, not measurements, for the owner to adjust. Kept here rather than
in `presets.py` so `ref-out/` does not move until they are approved. Kyoko is
Satoko before the cataclysm (`presets._before`), so she takes Satoko's value.
Katherina (14) and Linnea (15) were proposed at zero; the owner set them at
0.2 and 0.3. The male presets stay at zero.

Writes `out/bust/female_overview.png`: every female character at the chibi,
the top row as they are now and the bottom row at the proposed value.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import DISPLAY_NAMES, PRESETS

PROPOSED = {
    # Her design brief asks for "a noticeable bust".
    "krista": 1.0,
    # Late 40s to mid 50s, "strong capable build".
    "chiyo": 0.6,
    # Adult; her robe front covers the line under the bust.
    "reika": 0.6,
    # Adult; her hair and her coat carry most of it.
    "keiko": 0.6,
    # Adult, practical and guarded. Kyoko follows her.
    "satoko": 0.5,
    "kyoko": 0.5,
    # "Slender strong build", an officer.
    "elara": 0.4,
    # 15 and 14: the owner's values, 2026-09-25, raised from zero.
    "linnea": 0.3,
    "katherina": 0.2,
}
SCALE = 2
TILE_H = 620


def figure(name: str, bust: float) -> Image.Image:
    p = replace(PRESETS[name], bust=bust)
    sk = c.skeleton_for(p)
    png = cairosvg.svg2png(
        bytestring=c.render_character(p, sk, background="#ffffff").encode(), scale=SCALE
    )
    im = Image.open(io.BytesIO(png)).convert("RGB")
    # Crop to the figure's own ink, so a tall hat does not shrink the rest.
    grey = im.convert("L").point(lambda v: 255 if v < 250 else 0)
    box = grey.getbbox()
    im = im.crop((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6))
    return im.resize((int(im.width * TILE_H / im.height), TILE_H), Image.LANCZOS)


def main() -> None:
    os.makedirs("out/bust", exist_ok=True)
    names = list(PROPOSED)
    rows = [
        [(figure(n, 0.0), f"{DISPLAY_NAMES.get(n, n)}  now") for n in names],
        [(figure(n, v), f"{DISPLAY_NAMES.get(n, n)}  {v:g}") for n, v in PROPOSED.items()],
    ]
    pad, head = 12, 22
    width = max(sum(t.width for t, _ in row) + pad * (len(row) + 1) for row in rows)
    sheet = Image.new("RGB", (width, 2 * (TILE_H + head + pad) + pad), (225, 225, 225))
    d = ImageDraw.Draw(sheet)
    y = pad
    for row in rows:
        x = pad
        for tile, label in row:
            d.text((x + 4, y + 4), label, fill=(0, 0, 0))
            sheet.paste(tile, (x, y + head))
            x += tile.width + pad
        y += TILE_H + head + pad
    sheet.save("out/bust/female_overview.png")
    print("out/bust/female_overview.png", sheet.size)


main()
