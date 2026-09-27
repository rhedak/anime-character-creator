"""D3 of `docs/detail-plan.md`: which age should each preset state?

A proposal for the owner, drawn now against proposed: every preset's face,
top row as it is (face age 0, the four aged characters with `aged()` baked
into their faces), bottom row at the proposed `face_age`. The aged four keep
their baked face and take `face_age = 1`, which renders the same as
`1 + years` on the un-aged face (tested). `../valley_of_mist/docs/characters.md`
gives few ages: Satoshi twenty and reading older, Tomohiro seventeen to
nineteen; the rest are by role, and the numbers here are guesses to correct.

Writes `out/detail/age_lineup.png`.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
PROPOSED = {
    "katherina": 0.0,
    "linnea": 0.0,
    "satoko": 0.5,
    "tomohiro": 0.6,
    "satoshi": 0.8,
    "viktor": 0.8,
    "krista": 1.0,
    "elara": 1.0,
    "kyoko": 1.0,
    "keiko": 1.0,
    "reika": 1.0,
    "haruto": 1.0,
    "reinhard": 1.0,
    "gero": 1.0,
    "chiyo": 1.0,
    "daizen": 1.0,
    "tenno": 1.0,
}
BAKED = {"gero": 0.55, "chiyo": 1.0, "daizen": 1.0, "tenno": 1.0}


def face(p: c.CharacterParams, label: str) -> Image.Image:
    p = replace(p, outfit=replace(p.outfit, hat_color=None))
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=2))).convert("RGB")
    r, cx, cy = sk.head_r * 2, sk.head_cx * 2, sk.head_cy * 2
    im = im.crop((int(cx - 1.3 * r), int(cy - 1.2 * r), int(cx + 1.3 * r), int(cy + 1.45 * r)))
    ImageDraw.Draw(im).text((3, 3), label, fill=(200, 0, 0))
    return im


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    names = list(PROPOSED)
    rows = [
        [face(PRESETS[n], f"{n} now" + (f" (aged {BAKED[n]})" if n in BAKED else "")) for n in names],
        [
            face(replace(PRESETS[n], face_age=PROPOSED[n]), f"{n} {PROPOSED[n] + BAKED.get(n, 0.0):.2f}")
            for n in names
        ],
    ]
    per = 9
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    blocks = [(i, min(i + per, len(names))) for i in range(0, len(names), per)]
    sheet = Image.new("RGB", (per * (tw + 4), len(blocks) * 2 * (th + 4) + 10), (190, 190, 190))
    y = 0
    for a, b in blocks:
        for r in rows:
            for i, t in enumerate(r[a:b]):
                sheet.paste(t, (i * (tw + 4), y))
            y += th + 4
        y += 10
    sheet.save(f"{OUT}/age_lineup.png")
    print(f"{OUT}/age_lineup.png", sheet.size)


if __name__ == "__main__":
    main()
