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
BASE = {}  # her face as the preset has it now
VARIANTS = [
    ("face_age 0.50", {}, {"face_age": 0.50}),
    ("face_age 0.65", {}, {"face_age": 0.65}),
    ("face_age 0.75 (now)", {}, {"face_age": 0.75}),
    ("face_age 0.85", {}, {"face_age": 0.85}),
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
