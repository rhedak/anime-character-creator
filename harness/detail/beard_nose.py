"""D3 of `docs/detail-plan.md`: the moustache against the nose.

The moustache's top edge and outer corner now follow the grown face: the
corner with the mouth, the top edge to just under the nose (`_BEARD_NOSE_GAP`),
settled by face maturity `_BEARD_NOSE_ONSET`. Top row: Gero across the face
age range, to look for a jump; bottom row: the three bearded men at their
proposed ages (`age_lineup.PROPOSED`, the aged ones counted from 1). Faces at
3x. Writes `out/detail/beard_nose.png`.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"


def face(p, label):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=3))).convert("RGB")
    r, cx, cy = sk.head_r * 3, sk.head_cx * 3, sk.head_cy * 3
    im = im.crop((int(cx - 1.0 * r), int(cy - 0.3 * r), int(cx + 1.0 * r), int(cy + 1.4 * r)))
    ImageDraw.Draw(im).text((3, 3), label, fill=(200, 0, 0))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    gero = PRESETS["gero"]
    top = [face(replace(gero, face_age=a), f"gero age {a}") for a in (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)]
    bottom = [
        face(replace(PRESETS["gero"], face_age=1.0), "gero 1.55"),
        face(replace(PRESETS["daizen"], face_age=1.0), "daizen 2.0"),
        face(replace(PRESETS["reinhard"], face_age=1.0), "reinhard 1.0"),
    ]
    tw = max(t.width for t in top + bottom)
    th = max(t.height for t in top + bottom)
    sheet = Image.new("RGB", (len(top) * (tw + 4), 2 * (th + 4)), (190, 190, 190))
    for j, row in enumerate((top, bottom)):
        for i, t in enumerate(row):
            sheet.paste(t, (i * (tw + 4), j * (th + 4)))
    sheet.save(f"{OUT}/beard_nose.png")
    print(f"{OUT}/beard_nose.png", sheet.size)


if __name__ == "__main__":
    main()
