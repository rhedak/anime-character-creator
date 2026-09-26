"""Does the tunic's bust match the bare breasts? (after `docs/bare-body-plan.md`)

The bare breasts became their own shape in step 4b (`_bare_breast_spine`: an
ellipse widest at the fullest point, dropping the fold's depth times 1.25,
outlined from the arm's inner corner). The tunic still draws the bust the way
the bust campaign left it: the torso's side bent out at the fullest point and
hanging from there (`_bust_shape(drape=True)`), with the line under it a
shallow fold (`_bust_lines`). This puts them side by side for each adult
woman, chest only, same scale:

1. the tunic as worn, every other garment off;
2. the base layer (tunic off);
3. the tunic again, with the bare breasts' outline drawn over it in red.

Writes `out/bare/tunic_vs_bare.png`.
"""

import dataclasses
import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

WOMEN = ("satoko", "chiyo", "keiko", "krista", "reika", "elara")
KEEP = ("tunic_color", "boot_color", "underwear_color", "skirt_color")
OFF = [f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name not in KEEP]
SCALE = 4


def crop(name: str, bare: bool, overlay: bool) -> Image.Image:
    p = PRESETS[name]
    p = replace(p, outfit=replace(p.outfit, **dict.fromkeys(OFF)))
    sk = c.skeleton_for(p)
    q = replace(p, outfit=replace(p.outfit, tunic_color=None)) if bare else p
    svg = c.render_character(q, sk, background="#ffffff")
    if overlay:
        spine = c._bare_breast_spine(sk, replace(p, outfit=replace(p.outfit, tunic_color=None)))
        d = " ".join(
            "M " + " L ".join(f"{sk.head_cx + s * x:.1f} {y:.1f}" for x, y in spine) for s in (-1, 1)
        )
        svg = svg.replace(
            "</svg>", f'<path d="{d}" fill="none" stroke="#e02020" stroke-width="{c._stroke_w(sk) * 0.5:.2f}" /></svg>'
        )
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    s, r, cx = SCALE, sk.head_r * SCALE, sk.head_cx * SCALE
    return im.crop((int(cx - 1.05 * r), int(sk.shoulder_y * s - 0.1 * r), int(cx + 1.05 * r), int(sk.waist_y * s + 0.3 * r)))


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    rows = [
        ("tunic as it is", [crop(n, False, False) for n in WOMEN]),
        ("bare (base layer)", [crop(n, True, False) for n in WOMEN]),
        ("tunic, bare outline in red", [crop(n, False, True) for n in WOMEN]),
    ]
    pad, head = 8, 20
    tw, th = rows[0][1][0].size
    sheet = Image.new("RGB", (pad + len(WOMEN) * (tw + pad), pad + len(rows) * (th + head + pad)), (200, 200, 200))
    d = ImageDraw.Draw(sheet)
    y = pad
    for label, tiles in rows:
        d.text((pad, y + 4), label + "   (" + ", ".join(WOMEN) + ")", fill=(0, 0, 0))
        x = pad
        for t in tiles:
            sheet.paste(t, (x, y + head))
            x += tw + pad
        y += th + head + pad
    sheet.save("out/bare/tunic_vs_bare.png")
    print("out/bare/tunic_vs_bare.png", sheet.size)


if __name__ == "__main__":
    main()
