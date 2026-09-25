"""The mannequin: the adults with nothing worn, the view the body's own shape is
judged in (`docs/bare-body-plan.md`, from step 2 on).

Through the real outfit route, not by stubbing the garment parts the way
`harness/bust/bare_proportions.py` did: every `*_color` of `Outfit` set to
`None`, the tunic included. Two things are stubbed, both base layer rather
than body: the underpants, and (from step 3) the base top. The boots stay on
until step 5 gives a bare foot. No anatomical detail is drawn; the project
draws none.

Adults only, by the list in `audit.py` (the strategy file's rule). Chibi
only: the realistic build is not judged in this plan.

Writes `out/bare/mannequin.png`: each figure whole, and under it the torso
at three times the size.
"""

import dataclasses
import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

ADULTS = ("satoko", "chiyo", "keiko", "krista", "reika", "elara", "gero", "daizen", "tenno")
COLOR_FIELDS = [
    f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name != "boot_color"
]
BASE_LAYER = ("_underpants", "_base_top")
SCALE = 3


def render(name: str) -> tuple[Image.Image, c.Skeleton]:
    p = PRESETS[name]
    p = replace(p, outfit=replace(p.outfit, **dict.fromkeys(COLOR_FIELDS)))
    sk = c.skeleton_for(p)
    saved = {n: getattr(c, n) for n in BASE_LAYER if hasattr(c, n)}
    try:
        for n in saved:
            setattr(c, n, lambda *a, **k: "")
        svg = c.render_character(p, sk, background="#ffffff")
    finally:
        for n, fn in saved.items():
            setattr(c, n, fn)
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    return im, sk


def column(name: str) -> Image.Image:
    im, sk = render(name)
    s, r, cx = SCALE, sk.head_r * SCALE, sk.head_cx * SCALE
    whole = im.crop((int(cx - 1.6 * r), 0, int(cx + 1.6 * r), int(sk.canvas_h * s)))
    whole = whole.resize((whole.width // 3, whole.height // 3), Image.LANCZOS)
    torso = im.crop(
        (int(cx - 1.3 * r), int((sk.shoulder_y - 0.4 * sk.head_r) * s), int(cx + 1.3 * r), int(sk.knee_y * s + 0.9 * r))
    )
    w = max(whole.width, torso.width)
    out = Image.new("RGB", (w, 18 + whole.height + torso.height), (230, 230, 230))
    ImageDraw.Draw(out).text((4, 3), name, fill=(0, 0, 0))
    out.paste(whole, ((w - whole.width) // 2, 18))
    out.paste(torso, ((w - torso.width) // 2, 18 + whole.height))
    return out


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    cols = [column(n) for n in ADULTS]
    pad = 8
    sheet = Image.new(
        "RGB", (sum(c_.width for c_ in cols) + pad * (len(cols) + 1), max(c_.height for c_ in cols) + 2 * pad), (200, 200, 200)
    )
    x = pad
    for col in cols:
        sheet.paste(col, (x, pad))
        x += col.width + pad
    sheet.save("out/bare/mannequin.png")
    print("out/bare/mannequin.png", sheet.size)


main()
