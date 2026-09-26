"""Keiko's lab coat against her bust (after `docs/tunic-bust-plan.md`, outer
layers). The coat is a traced cut, fitted off a reference whose bust was not
hers, and answers the bust only through the body mapping (`_body_knots`, the
drape's `_bust_bulge` widening every row in proportion). Beside it: her dress
alone (the tunic, whose line and side now follow the bare breast), her bare
figure in the base layer, the coat with the bare outline in red, and Kyoko's
open coat, the parametric one that now parts over the bust.

Then the proposal on both coats: the tunic's curve carried across the
panels at the robe's lighter weight.

Chest at 4x, chibi. Writes `out/bare/keiko_coat.png`.
"""

import dataclasses
import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

SCALE = 4


def crop(p: c.CharacterParams, overlay: bool = False) -> Image.Image:
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    if overlay:
        bare = replace(p, outfit=replace(p.outfit, tunic_color=None))
        spine = c._bare_breast_spine(sk, bare)
        d = " ".join("M " + " L ".join(f"{sk.head_cx + s * x:.1f} {y:.1f}" for x, y in spine) for s in (-1, 1))
        svg = svg.replace(
            "</svg>", f'<path d="{d}" fill="none" stroke="#e02020" stroke-width="{c._stroke_w(sk) * 0.5:.2f}" /></svg>'
        )
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    s, r, cx = SCALE, sk.head_r * SCALE, sk.head_cx * SCALE
    return im.crop((int(cx - 1.15 * r), int(sk.shoulder_y * s - 0.15 * r), int(cx + 1.15 * r), int(sk.waist_y * s + 0.5 * r)))


def with_coat_line(p: c.CharacterParams) -> Image.Image:
    """The proposal: the tunic's curve carried across an open coat's panels at
    the robe's lighter weight (`_bust_fold`, `_ROBE_BUST_LINE`), so what shows
    in the opening joins into one curve passing under the lapel."""
    coat, traced = c._coat, c._traced_coat_and_belt

    def fold(sk: c.Skeleton) -> str:
        return c._bust_fold(sk, c._ROBE_BUST_LINE)

    def coat_with_line(sk, q):
        out = coat(sk, q)
        return out + fold(sk) if out else out

    def traced_with_line(sk, q, after_arms=True):
        out = traced(sk, q, after_arms=after_arms)
        return out + fold(sk) if out and not after_arms else out

    try:
        c._coat, c._traced_coat_and_belt = coat_with_line, traced_with_line
        return crop(p)
    finally:
        c._coat, c._traced_coat_and_belt = coat, traced


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    keiko = PRESETS["keiko"]
    no_coat = replace(keiko, outfit=replace(keiko.outfit, coat_color=None, coat_cut=None))
    keep = ("boot_color", "underwear_color")
    off = {f.name: None for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name not in keep}
    bare = replace(keiko, outfit=replace(keiko.outfit, **off))
    tiles = [
        ("Keiko, lab coat", crop(keiko)),
        ("Keiko, dress only", crop(no_coat)),
        ("Keiko, base layer", crop(bare)),
        ("lab coat, bare outline red", crop(keiko, overlay=True)),
        ("Kyoko, open coat", crop(PRESETS["kyoko"])),
        ("proposal: Keiko, line across the coat", with_coat_line(keiko)),
        ("proposal: Kyoko, line across the coat", with_coat_line(PRESETS["kyoko"])),
    ]
    pad, head = 8, 20
    tw = max(t.width for _, t in tiles)
    th = max(t.height for _, t in tiles)
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (tw + pad), pad + rows * (th + head + pad)), (200, 200, 200))
    d = ImageDraw.Draw(sheet)
    for i, (label, t) in enumerate(tiles):
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + head + pad)
        d.text((x, y), label, fill=(0, 0, 0))
        sheet.paste(t, (x, y + head))
    sheet.save("out/bare/keiko_coat.png")
    print("out/bare/keiko_coat.png", sheet.size)


if __name__ == "__main__":
    main()
