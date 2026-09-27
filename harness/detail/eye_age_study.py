"""D3 follow-up: how much should the face's age change the eye?

The owner, on the rebuilt Everglow cover: eye sizes should not differ this
dramatically within one story; scaling them is fine, but as its own choice.
Measured (Satoko): the eye's area falls to 0.87 at age 0.4, 0.70 at 1, 0.46
at 2, from two terms that stack: maturity's share of the adult build's eye
change (`_MATURE_EYE_SHARE`, 0.5) and `aged_face`'s eye terms above 1.

Rows, how much of the age's eye change is kept:
- **A** as now;
- **B** light: maturity's eye share 0.2, `aged_face`'s eye terms at a third;
- **C** none: the eye keeps its size and shape with age and only sits lower
  (`_MATURE_EYE_DROP`), its size left to `FaceStyle.eye_size`.

Columns: the Everglow pair (Linnea at 0.4, Gero at 1.55), Katherina at 0.35,
and part of the Valley cast at their ages. Each face is labelled with its eye
area against the chibi face's. Writes `out/detail/eye_age_study.png`.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
SHARE = c._MATURE_EYE_SHARE
AGED = c.aged_face
CAST = (
    ("linnea", 0.4),
    ("gero", None),
    ("katherina", 0.35),
    ("kyoko", None),
    ("satoshi", None),
    ("krista", None),
    ("reinhard", None),
    ("tenno", None),
    ("chiyo", None),
)


def aged_scaled(k: float):
    def aged(face, years=1.0):
        a = AGED(face, years)
        return replace(
            a,
            eye_size=face.eye_size + (a.eye_size - face.eye_size) * k,
            eye_openness=face.eye_openness + (a.eye_openness - face.eye_openness) * k,
            eye_lower_lid=face.eye_lower_lid + (a.eye_lower_lid - face.eye_lower_lid) * k,
            iris_size=face.iris_size + (a.iris_size - face.iris_size) * k,
        )

    return aged


def area(p) -> float:
    def one(q):
        sk = c.skeleton_for(q)
        _dx, _y, er, f = c._eye_placement(sk, q)
        return (er * f.eye_width / sk.head_r) * (er * (f.eye_openness + f.eye_lower_lid) / sk.head_r)

    return one(p) / one(replace(p, face_age=0.0))


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
        for tag, share, k in (("A now", SHARE, 1.0), ("B light", 0.2, 1 / 3), ("C none", 0.0, 0.0)):
            c._MATURE_EYE_SHARE, c.aged_face = share, aged_scaled(k)
            row = []
            for n, age in CAST:
                p = PRESETS[n] if age is None else replace(PRESETS[n], face_age=age)
                row.append(face(p, f"{tag}: {n} {p.face_age:g}, eye {area(p):.2f}"))
            rows.append(row)
    finally:
        c._MATURE_EYE_SHARE, c.aged_face = SHARE, AGED
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(rows[0]) * (tw + 3), len(rows) * (th + 5)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 3), j * (th + 5)))
    sheet.save(f"{OUT}/eye_age_study.png")
    print(f"{OUT}/eye_age_study.png", sheet.size)


if __name__ == "__main__":
    main()
