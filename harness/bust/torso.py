"""The body layer on its own: every garment part switched off, so what is left
is `_torso`, the neck, the head, the arms and the legs (`docs/bust-plan.md`,
step 3).

Unlike `bare.py`, which paints the tunic in the skin tone because there was no
body to show, this is the body itself. The arms and legs still wear whatever
their own parts draw (a sleeve, a boot), since those are not separable yet.

Writes `out/bust/torso.png`: Satoko and Keiko at the chibi and Satoko at the
realistic build, each at `bust` 0 and 1.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

GARMENTS = (
    "_tunic",
    "_skirt",
    "_underskirt",
    "_hakama",
    "_hanging_sleeves",
    "_robe_front",
    "_placket",
    "_chest_pockets",
    "_strap",
    "_apron",
    "_belt",
    "_collar",
    "_coat",
    "_pouches",
    "_crystal_harness",
    "_katana",
    "_staff",
    "_traced_coat_and_belt",
)
SCALE = 2
TILE = 560


def body_only(preset: str, bust: float, build: str | None) -> Image.Image:
    p = replace(PRESETS[preset], bust=bust)
    if build == "realistic":
        p = replace(p, body=None, heads=c.BUILDS["realistic"])
    sk = c.skeleton_for(p)
    saved = {name: getattr(c, name) for name in GARMENTS}
    try:
        for name in GARMENTS:
            setattr(c, name, lambda *a, **k: "")
        svg = c.render_character(p, sk, background="#ffffff")
    finally:
        for name, fn in saved.items():
            setattr(c, name, fn)
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE)))
    cx, cy, r = sk.head_cx * SCALE, sk.head_cy * SCALE, sk.head_r * SCALE
    half = max(1.7 * r, (sk.arm_x + sk.arm_half_w * 2.0) * SCALE - cx)
    bottom = (sk.hip_y + 0.8 * sk.head_r) * SCALE
    return im.convert("RGB").crop((int(cx - half), int(cy - 1.4 * r), int(cx + half), int(bottom)))


def main() -> None:
    os.makedirs("out/bust", exist_ok=True)
    tiles = []
    for preset, build in (("satoko", None), ("keiko", None), ("satoko", "realistic")):
        for bust in (0.0, 1.0):
            im = body_only(preset, bust, build)
            im = im.resize((int(im.width * TILE / im.height), TILE), Image.LANCZOS)
            tiles.append((im, f"{preset} {build or 'chibi'}  bust {bust}"))
    pad, head = 10, 22
    sheet = Image.new(
        "RGB", (sum(t.width for t, _ in tiles) + pad * (len(tiles) + 1), TILE + head + 2 * pad), (225, 225, 225)
    )
    d = ImageDraw.Draw(sheet)
    x = pad
    for im, label in tiles:
        d.text((x + 4, pad + 4), label, fill=(0, 0, 0))
        sheet.paste(im, (x, pad + head))
        x += im.width + pad
    sheet.save("out/bust/torso.png")
    print("out/bust/torso.png", sheet.size)


main()
