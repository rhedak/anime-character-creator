"""The body with its garments off, against the canon's proportions, to settle
how high the bust sits (`docs/bust-plan.md`, step 7; the owner's question,
2026-09-25, whether Krista's read "too low").

Every garment part switched off, as `torso.py` does, and the arms drawn at a
third so the torso's side shows through them. Over it, across the torso:

- grey: the shoulder line and the waist;
- blue: the canon's nipple line (50% of the way from the shoulder line to the
  waist) and its under-bust fold (62%), standard figure-drawing proportions;
- red: where ours are, the fullest point (`bust_y`) and the fold the line under
  the bust is drawn at.

Adults only (Satoko at 0.5, Krista at 1.0), at three values of `_BUST_ALONG`.
No anatomical detail is drawn: the project draws none, and the question is
the silhouette's proportions.

Writes `out/bust/bare_proportions.png`.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator import skeleton
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
ALONGS = (0.30, 0.20, 0.15)
CASES = (("satoko", 0.5), ("krista", 1.0))
SCALE = 3


def render(name: str, bust: float, along: float) -> Image.Image:
    skeleton._BUST_ALONG = along
    p = replace(PRESETS[name], bust=bust)
    sk = c.skeleton_for(p)
    saved = {n: getattr(c, n) for n in (*GARMENTS, "_arms")}
    arms = c._arms
    try:
        for n in GARMENTS:
            setattr(c, n, lambda *a, **k: "")
        c._arms = lambda *a, **k: f'<g opacity="0.33">{arms(*a, **k)}</g>' if not k.get("silhouette") else arms(*a, **k)
        svg = c.render_character(p, sk, background="#ffffff")
    finally:
        for n, fn in saved.items():
            setattr(c, n, fn)
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    d = ImageDraw.Draw(im)
    cx, r = sk.head_cx * SCALE, sk.head_r * SCALE
    x0, x1 = cx - 1.2 * r, cx + 1.2 * r
    run = sk.waist_y - sk.shoulder_y
    body = c._bust_shape(sk)
    fold = body.peak[1] + (body.outline[1][1][1] - body.peak[1]) * 0.85
    for y, colour in (
        (sk.shoulder_y, (150, 150, 150)),
        (sk.waist_y, (150, 150, 150)),
        (sk.shoulder_y + run * 0.50, (40, 90, 220)),
        (sk.shoulder_y + run * 0.62, (40, 90, 220)),
        (sk.bust_y, (220, 40, 40)),
        (fold, (220, 40, 40)),
    ):
        d.line((x0, y * SCALE, x1, y * SCALE), fill=colour, width=2)
    label = (
        f"{name} {bust:g}, along {along:.2f}: fullest {(sk.bust_y - sk.shoulder_y) / run:.0%},"
        f" fold {(fold - sk.shoulder_y) / run:.0%}"
    )
    im = im.crop((int(x0), int(sk.head_cy * SCALE - 1.3 * r), int(x1), int(sk.hip_y * SCALE + 0.4 * r)))
    out = Image.new("RGB", (im.width, im.height + 22), (230, 230, 230))
    out.paste(im, (0, 22))
    ImageDraw.Draw(out).text((4, 5), label, fill=(0, 0, 0))
    return out


def main() -> None:
    os.makedirs("out/bust", exist_ok=True)
    rows = [[render(n, v, a) for a in ALONGS] for n, v in CASES]
    skeleton._BUST_ALONG = 0.30
    pad = 10
    w = max(sum(t.width for t in row) + pad * (len(row) + 1) for row in rows)
    h = sum(row[0].height + pad for row in rows) + pad
    sheet = Image.new("RGB", (w, h), (200, 200, 200))
    y = pad
    for row in rows:
        x = pad
        for tile in row:
            sheet.paste(tile, (x, y))
            x += tile.width + pad
        y += row[0].height + pad
    sheet.save("out/bust/bare_proportions.png")
    print("out/bust/bare_proportions.png", sheet.size)


main()
