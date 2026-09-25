"""The base-layer view: what the tool shows with the tunic off
(`docs/bare-body-plan.md`, from step 3 on). The whole cast, at the chibi, in
two rows: the tunic off and everything else as the preset wears it; then
every optional garment off too, the boots and the underwear kept.

Every character, since every one wears the base layer; the fully bare
mannequin is `mannequin.py`, adults only.

Writes `out/bare/base_layer.png`.
"""

import dataclasses
import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

KEEP = ("boot_color", "underwear_color")
OPTIONAL = [f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name not in KEEP]
SCALE = 1


def figure(p: c.CharacterParams) -> Image.Image:
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    r, cx = sk.head_r * SCALE, sk.head_cx * SCALE
    return im.crop((int(cx - 1.7 * r), 0, int(cx + 1.7 * r), im.height))


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    rows = []
    for label, change in (
        ("tunic off", lambda o: replace(o, tunic_color=None)),
        ("everything off but boots and underwear", lambda o: replace(o, **dict.fromkeys(OPTIONAL))),
    ):
        rows.append((label, [(n, figure(replace(p, outfit=change(p.outfit)))) for n, p in PRESETS.items()]))
    pad, head = 6, 16
    tw, th = rows[0][1][0][1].size
    n = len(PRESETS)
    sheet = Image.new("RGB", (pad + n * (tw + pad), pad + len(rows) * (th + 2 * head + pad)), (215, 215, 215))
    d = ImageDraw.Draw(sheet)
    y = pad
    for label, tiles in rows:
        d.text((pad, y + 2), label, fill=(0, 0, 0))
        x = pad
        for name, t in tiles:
            d.text((x + 2, y + head + 2), name, fill=(0, 0, 0))
            sheet.paste(t, (x, y + 2 * head))
            x += tw + pad
        y += th + 2 * head + pad
    sheet.save("out/bare/base_layer.png")
    print("out/bare/base_layer.png", sheet.size)


main()
