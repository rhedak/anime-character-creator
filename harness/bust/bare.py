"""The figure without clothes, to judge body proportions rather than garments.

A bust is a property of the body, and every earlier sweep judged it through a
tunic, which has its own shape. This strips the outfit to skin so the torso's
own silhouette is what is on the page (`docs/bust-plan.md`, B0).

**There is no body layer to strip to.** This project has no `_torso` or `_body`
part: `_tunic` is the torso, and `tunic_color` is not even optional. So "bare"
here means the same shapes drawn in the skin tone, and what that shows is the
body exactly as the generator conceives it, which is the thing worth knowing
before deciding what a bust should do to it.

No anatomical detail is drawn and none is added here: this project draws none
by design, and the point is the silhouette.

Writes `out/bust/bare.png` and prints the torso's widths in head radii.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

VALUES = (0.0, 0.5, 1.0)
SCALE = 2
TILE = 560


def bare(preset: str, bust: float, build: str | None = None):
    p = PRESETS[preset]
    skin = p.skin_tone
    p = replace(
        p,
        bust=bust,
        outfit=replace(
            p.outfit,
            tunic_color=skin,
            undersleeve_color=skin,
            boot_color=skin,
            skirt_color=None,
            trouser_color=None,
            belt_color=None,
            coat_color=None,
            coat_cut=None,
            coat_sleeves=False,
            skirt_cut=None,
            collar_color=None,
            apron_color=None,
            underskirt_color=None,
            pouch_color=None,
            sleeve_long=False,
            # Nothing left to tuck into once the skirt is gone: tucked, the hem
            # stops short and the page shows between it and the legs.
            tunic_tucked=False,
            katana_color=None,
        ),
    )
    if build == "realistic":
        p = replace(p, body=None, heads=c.BUILDS["realistic"])
    sk = c.skeleton_for(p)
    png = cairosvg.svg2png(
        bytestring=c.render_character(p, sk, background="#ffffff").encode(), scale=SCALE
    )
    im = Image.open(io.BytesIO(png)).convert("RGB")
    cx, cy, r = sk.head_cx * SCALE, sk.head_cy * SCALE, sk.head_r * SCALE
    # Down past the hip whatever the build. A fixed 4.2 head radii stopped the
    # realistic row at the collarbone, and it was reported on as if its torso
    # had been seen (`docs/bust-strategy.md`).
    bottom = max(cy + 4.2 * r, (sk.hip_y + 0.6 * sk.head_r) * SCALE)
    half = max(1.7 * r, (sk.arm_x + sk.arm_half_w * 2.0) * SCALE - cx)
    return im.crop((int(cx - half), int(cy - 1.4 * r), int(cx + half), int(bottom))), sk


def main() -> None:
    os.makedirs("out/bust", exist_ok=True)
    rows = []
    for preset, build in (("satoko", None), ("keiko", None), ("satoko", "realistic")):
        tiles = []
        for v in VALUES:
            im, sk = bare(preset, v, build)
            im = im.resize((int(im.width * TILE / im.height), TILE), Image.LANCZOS)
            tiles.append((im, f"{preset} {build or 'chibi'}  bust {v}"))
        rows.append(tiles)
    tw = max(t.width for row in rows for t, _ in row)
    head = 24
    sheet = Image.new(
        "RGB", (3 * tw + 4 * 10, len(rows) * (TILE + head + 10) + 10), (225, 225, 225)
    )
    d = ImageDraw.Draw(sheet)
    for r, row in enumerate(rows):
        y = 10 + r * (TILE + head + 10)
        for i, (tile, label) in enumerate(row):
            x = 10 + i * (tw + 10)
            d.text((x + 4, y + 5), label, fill=(0, 0, 0))
            sheet.paste(tile, (x, y + head))
    sheet.save("out/bust/bare.png")
    print("out/bust/bare.png", sheet.size)

    print("\ntorso, in head radii (half-widths):")
    for preset in ("satoko", "keiko"):
        for build in (None, "realistic"):
            _, sk = bare(preset, 0.0, build)
            w = lambda v: v / sk.head_r  # noqa: E731
            print(
                f"  {preset:7s} {build or 'chibi':9s} shoulder {w(sk.shoulder_half_w):.3f}"
                f"  bust reach {w(sk.bust_reach):.3f}  waist {w(sk.waist_half_w):.3f}"
                f"  hip {w(sk.hip_half_w):.3f}  arm inner {w(sk.arm_x - sk.arm_half_w):.3f}"
            )


main()
