"""Step 7 of `docs/bare-body-plan.md`: the cast across skin tones.

A row per tone, very light to very dark, the candidate swatches for the web
tool; a column per character, in the base-layer view (tunic, boots and every
optional garment off, the underwear on), so the skin shows on the whole body
rather than a face and two hands. Checks what `CLAUDE.md` asks of any palette
far from the defaults: that the outline still reads against the skin, and
that what sits on the skin (the blush, a fixed pink at an opacity; the line
under the bust, the chest lines, the navel, all in the outline colour) holds
up at both ends.

Krista (bust, top, blush), Gero (beard, chest lines), Satoko (scar), Linnea
(a younger figure, in the base layer). Writes `out/bare/skin_tones.png`.
"""

import dataclasses
import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

TONES = (
    ("very light", "#fbe6d6"),
    ("light (default)", "#f2c9a1"),
    ("light warm", "#e6b38a"),
    ("medium", "#c98d62"),
    ("medium dark", "#a8704a"),
    ("dark", "#865335"),
    ("very dark", "#633a24"),
    ("deepest", "#442617"),
)
NAMES = ("krista", "gero", "satoko", "linnea")
OFF = [f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name != "underwear_color"]
SCALE = 2


def tile(name: str, tone: str) -> Image.Image:
    p = PRESETS[name]
    p = replace(p, skin_tone=tone, outfit=replace(p.outfit, **dict.fromkeys(OFF)))
    sk = c.skeleton_for(p)
    im = Image.open(
        io.BytesIO(cairosvg.svg2png(bytestring=c.render_character(p, sk, background="#ffffff").encode(), scale=SCALE))
    ).convert("RGB")
    s, r, cx = SCALE, sk.head_r * SCALE, sk.head_cx * SCALE
    return im.crop((int(cx - 1.5 * r), int((sk.head_cy - 1.0 * sk.head_r) * s), int(cx + 1.5 * r), int(sk.hip_y * s + 1.2 * r)))


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    rows = [(f"{label} {hexv}", [tile(n, hexv) for n in NAMES]) for label, hexv in TONES]
    pad, lab = 6, 120
    tw, th = rows[0][1][0].size
    sheet = Image.new("RGB", (lab + len(NAMES) * (tw + pad), len(rows) * (th + pad) + pad), (215, 215, 215))
    d = ImageDraw.Draw(sheet)
    y = pad
    for label, tiles in rows:
        d.text((4, y + th // 2), label, fill=(0, 0, 0))
        x = lab
        for t in tiles:
            sheet.paste(t, (x, y))
            x += tw + pad
        y += th + pad
    sheet.save("out/bare/skin_tones.png")
    print("out/bare/skin_tones.png", sheet.size)


if __name__ == "__main__":
    main()
