"""Her face beside variants of ours (`docs/mio-plan.md`, M9): the reference first, then each
variant, cropped to the face at one head scale.

    ./harness/run.sh harness/mio/face_compare.py            # the variants in VARIANTS below
"""

import sys
from dataclasses import replace

from compare import R, _SLENDER_HEAD_SCALE, ours, reference
from PIL import Image, ImageDraw

from anime_character_creator.presets import MIO

BOX = (500, 215, 760, 420)
K = 3

# (label, {FaceStyle field: value}, {CharacterParams field: value})
# Solved against her measurements (`eye_metrics.py`, `measure_eyes.py`): the aperture, the iris's
# diameter, the distance between the eyes and the white on the outer side only.
MATCHED = {
    "eye_size": 1.009, "eye_width": 0.729, "eye_openness": 1.0, "eye_lower_lid": 1.0,
    "iris_size": 0.978, "eye_gap": 1.157, "iris_inset": 1.0, "eye_tilt": -0.05,
}
TALL = dict(MATCHED, iris_aspect=1.37)
VARIANTS = [
    ("now", {}, {}),
    ("matched, tall iris", dict(TALL, eye_corner=0.0), {}),
    ("matched, tall iris, lash 1.2", dict(TALL, eye_corner=0.0, lash=1.2), {}),
    ("matched, tall iris, corner 0.2, lash 1.2", dict(TALL, eye_corner=0.2, lash=1.2), {}),
]


def make(face, params):
    return replace(MIO, face=replace(MIO.face, **face), **params)


def run(variants, out="out/mio/face_variants.png"):
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
