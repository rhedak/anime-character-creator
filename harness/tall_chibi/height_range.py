"""R4b of `docs/tall-chibi-plan.md`: the height slider across its range.

Characters chosen for the parts most likely to misbehave when the body below
the shoulders stretches: Satoko (skirt, apron, pouches), Satoshi (trousers,
katana), Krista (bust, strap, crystals, tall boots), Keiko (the traced lab
coat), Kyoko (the long parametric coat), Reika (robe front, hakama),
Katherina (the `tall_chibi` body, hat, staff, familiar, traced jacket), and
Krista again in the base layer, barefoot. Each at 0.8, 1.0 and 1.3, drawn at
one head size with the feet on one line, which is how a height reads.

Also reports, per render, whether the figure's ink touches its own canvas's
edge, since a taller figure is fitted to a fixed canvas.

Writes `out/tall_chibi/height_range.png`.
"""

import dataclasses
import io
import os
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

HEIGHTS = (0.8, 1.0, 1.3)
OFF = [
    f.name
    for f in dataclasses.fields(c.Outfit)
    if f.name.endswith("_color") and f.name not in ("underwear_color",)
]


def cases() -> list[tuple[str, c.CharacterParams]]:
    krista = PRESETS["krista"]
    bare = replace(krista, outfit=replace(krista.outfit, **dict.fromkeys(OFF)))
    return [(n, PRESETS[n]) for n in ("satoko", "satoshi", "krista", "keiko", "kyoko", "reika", "katherina")] + [
        ("krista bare", bare)
    ]


def render(p: c.CharacterParams, h: float) -> tuple[Image.Image, c.Skeleton, bool]:
    q = replace(p, height=h)
    sk = c.skeleton_for(q)
    svg = c.render_character(q, sk)
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGBA")
    a = np.array(im)[:, :, 3]
    touches = bool(a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any())
    white = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return Image.alpha_composite(white, im).convert("RGB"), sk, touches


def main() -> None:
    os.makedirs("out/tall_chibi", exist_ok=True)
    ref_r = c.skeleton_for(PRESETS["satoko"]).head_r
    tiles, notes = [], []
    for name, p in cases():
        for h in HEIGHTS:
            im, sk, touches = render(p, h)
            if touches:
                notes.append(f"{name} at {h}: ink reaches the canvas edge")
            k = ref_r / sk.head_r
            im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
            foot, cx = sk.foot_y * k, sk.head_cx * k
            w, top = int(2.6 * ref_r), int(foot - 11.5 * ref_r)
            tile = Image.new("RGB", (w, int(12.2 * ref_r)), (255, 255, 255))
            crop = im.crop((int(cx - w / 2), max(0, top), int(cx + w / 2), min(im.height, int(foot + 0.6 * ref_r))))
            tile.paste(crop, (0, max(0, -top)))
            ImageDraw.Draw(tile).text((3, 3), f"{name} {h}", fill=(0, 0, 0))
            tiles.append(tile)
    cols = len(HEIGHTS) * 4
    tw, th = tiles[0].size
    pad = 5
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (tw + pad), pad + rows * (th + pad)), (200, 200, 200))
    for i, t in enumerate(tiles):
        sheet.paste(t, (pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + pad)))
    sheet.save("out/tall_chibi/height_range.png")
    print("out/tall_chibi/height_range.png", sheet.size)
    print("\n".join(notes) or "no figure reaches its canvas edge")


if __name__ == "__main__":
    main()
