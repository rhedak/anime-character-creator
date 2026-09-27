"""D3 follow-up: the space between the eyes against the eyes' size.

The owner, on the rebuilt Everglow cover: Gero's eyes read much farther apart
than Linnea's. Measured: their centres are nearly as far apart (0.85 and
0.88 head radii), but his eyes are smaller (`eye_size` 0.86 against 0.98), so
the gap between them is 0.56 of an eye's width against her 0.36. The spacing
(`_eye_placement`'s `eye_dx`) does not follow the eye's size.

Variants move the centres so the gap follows the eye's width: `eye_dx =
dx + k * (w * (1 + G) - dx)`, with `w` the eye's half-width, `G` the cast's
median gap against its eye width, and k 0 (today), 0.5 and 1 (the gap always
the default's share of the eye). Columns: the Everglow pair, Katherina and
part of the Valley cast at their ages, each labelled with its gap against its
eye width. Writes `out/detail/eye_spacing_study.png`.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
PLACE = c._eye_placement
CAST = ("linnea", "gero", "katherina", "kyoko", "satoshi", "krista", "reinhard", "tenno", "chiyo")


def cast_ratio() -> float:
    """The cast's median gap against its eye width, today. The default face's
    own (0.58) sits at Gero's end, its eye being narrower than most presets',
    and would have moved everyone else's eyes apart instead of his in."""
    ratios = []
    for p in PRESETS.values():
        sk = c.skeleton_for(p)
        dx, _y, er, f = PLACE(sk, p)
        w = er * f.eye_width * c._EYE_ASPECT
        ratios.append((dx - w) / w)
    ratios.sort()
    return ratios[len(ratios) // 2]


G = cast_ratio()


def with_k(k: float):
    def place(sk, p):
        dx, y, er, f = PLACE(sk, p)
        w = er * f.eye_width * c._EYE_ASPECT
        return dx + k * (w * (1 + G) - dx), y, er, f

    return place


def gap_ratio(p) -> float:
    sk = c.skeleton_for(p)
    dx, _y, er, f = c._eye_placement(sk, p)
    w = er * f.eye_width * c._EYE_ASPECT
    return (dx - w) / w


def face(p, label):
    p = replace(p, outfit=replace(p.outfit, hat_color=None))
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=2))).convert("RGB")
    r, cx, cy = sk.head_r * 2, sk.head_cx * 2, sk.head_cy * 2
    im = im.crop((int(cx - 1.25 * r), int(cy - 0.9 * r), int(cx + 1.25 * r), int(cy + 1.3 * r)))
    ImageDraw.Draw(im).text((3, 3), label, fill=(200, 0, 0))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    try:
        for k in (0.0, 0.5, 1.0):
            c._eye_placement = with_k(k)
            rows.append([face(PRESETS[n], f"k {k}: {n}, gap/eye {gap_ratio(PRESETS[n]):.2f}") for n in CAST])
    finally:
        c._eye_placement = PLACE
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(rows[0]) * (tw + 3), len(rows) * (th + 5)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 3), j * (th + 5)))
    sheet.save(f"{OUT}/eye_spacing_study.png")
    print(f"{OUT}/eye_spacing_study.png", sheet.size, "cast median gap/eye", round(G, 3))


if __name__ == "__main__":
    main()
