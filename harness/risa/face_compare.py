"""Her face beside variants of ours (`docs/risa-plan.md`, M9): the reference first, then each
variant, cropped to the face at one head scale.

    ./harness/run.sh harness/risa/face_compare.py            # the variants in VARIANTS below
"""

import sys
from dataclasses import replace

from compare import R, _SLENDER_HEAD_SCALE, ours, reference
from PIL import Image, ImageDraw

from anime_character_creator.presets import RISA

BOX = (500, 215, 760, 420)
K = 3

# (label, {FaceStyle field: value}, {CharacterParams field: value})
# Solved against her measurements (`eye_metrics.py`, `measure_eyes.py`): the aperture, the iris's
# diameter, the distance between the eyes and the white on the outer side only.
MATCHED = {
    "eye_size": 1.009, "eye_width": 0.729, "eye_openness": 1.0, "eye_lower_lid": 1.0,
    "iris_size": 0.978, "eye_gap": 1.157, "iris_inset": 1.0, "eye_tilt": -0.05,
}
SOFT = dict(lid_shadow=0.12, lash=1.6, nose_dot=True, mouth_curve=0.5, mouth_width=0.5)
DEEP = {"eye_color": "#3c7a50"}
VARIANTS = [
    ("now", {}, {}),
    ("A soft: lid shadow, lash 1.6, dot nose, slight smile", dict(SOFT), {}),
    ("B + darker green", dict(SOFT), dict(DEEP)),
    ("C + lid over the iris (open 0.88, aspect 1.5)", dict(SOFT, eye_openness=0.88, iris_aspect=1.5), dict(DEEP)),
    ("D + brows lifted (tilt -0.25), smile 0.8", dict(SOFT, eye_openness=0.88, iris_aspect=1.5, brow_tilt=-0.25, mouth_curve=0.8), dict(DEEP)),
]


def make(face, params):
    return replace(RISA, face=replace(RISA.face, **face), **params)


def run(variants, out="out/risa/face_variants.png"):
    ref = reference().crop(BOX)
    tiles = [("reference", ref)]
    for label, face, params in variants:
        tiles.append((label, ours(make(face, params), reference().size, r=R * _SLENDER_HEAD_SCALE).crop(BOX)))
    w, h = ref.size
    cols = min(len(tiles), 3)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (w * K * cols, (h * K + 24) * rows), "white")
    for i, (label, im) in enumerate(tiles):
        x, y = (i % cols) * w * K, (i // cols) * (h * K + 24)
        sheet.paste(im.resize((w * K, h * K), Image.LANCZOS), (x, y + 24))
        ImageDraw.Draw(sheet).text((x + 8, y + 6), label, fill="black")
    sheet.save(out)
    print(f"wrote {out} ({sheet.size[0]} x {sheet.size[1]})")


if __name__ == "__main__":
    run(VARIANTS)
