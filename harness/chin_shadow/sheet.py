"""Deferred item, small skin shadows (`docs/detail-plan.md`, decision 2: skin
stays flat, the shadows an optional polish pass): the one under the chin,
`FaceStyle.chin_shadow`, off and at a few depths and tones.

Rows are characters (and two skin tones far from the cast's, very light and
very dark, for `shade()`), columns the variants. Cropped to the face and neck.

    ./harness/run.sh harness/chin_shadow/sheet.py

Written to `out/chin_shadow/sheet.png`.
"""

import io
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/chin_shadow"
WHO = ["satoko", "reika", "satoshi", "krista", "chiyo", "katherina"]
SKINS = {"very light": "#fbe7d9", "very dark": "#6b4430"}
# (label, drop, value): off first, then the depth, then the tone.
VARIANTS = [
    ("off", None, None),
    ("drop 0.10", 0.10, 0.88),
    ("drop 0.16", 0.16, 0.88),
    ("drop 0.22", 0.22, 0.88),
    ("0.16, darker 0.80", 0.16, 0.80),
]
BOX = (-1.1, -0.2, 1.1, 1.75)
SCALE = 2.0


def render(p, drop, value):
    if drop is not None:
        c._CHIN_SHADOW_DROP, c._CHIN_SHADOW_VALUE = drop, value
        p = replace(p, face=replace(p.face, chin_shadow=True))
    p = replace(p, familiar_color=None, outfit=replace(p.outfit, hat_color=None, hat_band_color=None))
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="white")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    cx, cy, r = sk.head_cx * SCALE, sk.head_cy * SCALE, sk.head_r * SCALE
    x0, y0, x1, y1 = BOX
    return im.crop((round(cx + x0 * r), round(cy + y0 * r), round(cx + x1 * r), round(cy + y1 * r)))


def main() -> None:
    people = [(k, PRESETS[k]) for k in WHO]
    people += [(k, replace(PRESETS["satoko"], skin_tone=v)) for k, v in SKINS.items()]
    rows = [(name, [render(p, d, v) for _, d, v in VARIANTS]) for name, p in people]
    tw, th = rows[0][1][0].size
    W = 90 + len(VARIANTS) * (tw + 6)
    H = 20 + len(rows) * (th + 6)
    out = Image.new("RGB", (W, H), (150, 150, 150))
    d = ImageDraw.Draw(out)
    for j, (label, _, _) in enumerate(VARIANTS):
        d.text((90 + j * (tw + 6) + 4, 4), label, fill=(0, 0, 0))
    for i, (name, tiles) in enumerate(rows):
        y = 20 + i * (th + 6)
        d.text((4, y + th // 2), name, fill=(0, 0, 0))
        for j, t in enumerate(tiles):
            out.paste(t, (90 + j * (tw + 6), y))
    out.save(f"{OUT}/sheet.png")
    print(f"{OUT}/sheet.png", out.size)


if __name__ == "__main__":
    main()
