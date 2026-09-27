"""D3 of `docs/detail-plan.md`, round two: prototypes of a longer chin and a lid
crease, both riding face maturity, for the owner to judge before either goes
into `src/`.

- **Chin.** `_head_pt` drops the chin by `0.05 * build`, all the retired
  adult build had; at one face width the reference's chin sits about 0.27
  head radii lower than ours (`docs/detail-status.md`, D0). The prototype adds
  `extra * maturity` to that drop, maturity read back off the face build (the
  figure's own build is always the chibi's now). Everything that follows the
  skull (the jaw line, the beard, the hair's inner edge, the glasses' arms)
  follows it, since they all read `_head_pt`.
- **Crease.** A thin line over the outer half of the lid, above the lash, its
  weight growing with maturity. D2 dropped it at maturity 0, where it crowded
  the brow; the older eye is smaller and leaves room.

Rows: no change; chin +0.10; chin +0.20; chin +0.10 with the crease.
Columns: Satoko at maturity 0.5 and 1, Katherina, Satoshi and Gero at 1.
Writes `out/detail/maturity_proto.png`.
"""

import io
import math
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
CHIBI_BUILD = c.skeleton_for(c.CharacterParams()).build
HEAD_PT, EYE = c._head_pt, c._eye
STATE = {"extra": 0.0, "crease": False, "maturity": 0.0}


def head_pt(deg: float, radius: float, build: float):
    x, y = HEAD_PT(deg, radius, build)
    mature = max(0.0, (build - CHIBI_BUILD) / (1.0 - CHIBI_BUILD))
    y0 = -math.cos(math.radians(deg)) * radius
    if STATE["extra"] and y0 > c._JAW_START_Y:
        lean = min(1.0, (y0 - c._JAW_START_Y) / (1.0 - c._JAW_START_Y))
        y *= 1.0 + STATE["extra"] * mature * lean
    return x, y


def eye(ex, ey, er, side, f, eye_color, sw, pupil_ratio=0.40):
    out = EYE(ex, ey, er, side, f, eye_color, sw, pupil_ratio)
    m = STATE["maturity"]
    if not (STATE["crease"] and m > 0):
        return out
    quads = c._eye_quads(er, f)
    lid = c._lid_points(quads, 0, 1)
    n = len(lid) - 1
    outer = c._LASH_INNER + (c._LASH_OUTER - c._LASH_INNER) * f.lash
    pts = []
    for i in range(int(n * 0.45), int(n * 0.92) + 1):
        a, b = lid[max(0, i - 1)], lid[min(n, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = ty / tl, -tx / tl
        if ny > 0:
            nx, ny = -nx, -ny
        s = i / n
        t = er * (c._LASH_INNER + (outer - c._LASH_INNER) * s**c._LASH_EASE) + er * 0.16
        pts.append((ex + side * (lid[i][0] + nx * t), ey + lid[i][1] + ny * t))
    d = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts)
    return out + (
        f'<path d="{d}" fill="none" stroke="{c.OUTLINE}" stroke-width="{c._interior_w(sw, 0.8 * m):.2f}" '
        f'stroke-linecap="round" />'
    )


def face(p: c.CharacterParams, label: str) -> Image.Image:
    STATE["maturity"] = p.face_maturity
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=3))).convert("RGB")
    r, cx, cy = sk.head_r * 3, sk.head_cx * 3, sk.head_cy * 3
    im = im.crop((int(cx - 1.35 * r), int(cy - 1.1 * r), int(cx + 1.35 * r), int(cy + 1.75 * r)))
    ImageDraw.Draw(im).text((3, 3), label, fill=(200, 0, 0))
    return im


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    k = PRESETS["katherina"]
    k = replace(k, outfit=replace(k.outfit, hat_color=None))
    cols = [
        ("satoko 0.5", replace(PRESETS["satoko"], face_maturity=0.5)),
        ("satoko 1", replace(PRESETS["satoko"], face_maturity=1.0)),
        ("katherina 1", replace(k, face_maturity=1.0)),
        ("satoshi 1", replace(PRESETS["satoshi"], face_maturity=1.0)),
        ("gero 1", replace(PRESETS["gero"], face_maturity=1.0)),
    ]
    rows_spec = (("as built", 0.0, False), ("chin +0.10", 0.10, False), ("chin +0.20", 0.20, False), ("chin +0.10, crease", 0.10, True))
    c._head_pt, c._eye = head_pt, eye
    try:
        rows = []
        for label, extra, crease in rows_spec:
            STATE["extra"], STATE["crease"] = extra, crease
            rows.append([face(p, f"{label} / {n}") for n, p in cols])
    finally:
        c._head_pt, c._eye = HEAD_PT, EYE
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(cols) * (tw + 4), len(rows) * (th + 4)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 4), j * (th + 4)))
    sheet.save(f"{OUT}/maturity_proto.png")
    print(f"{OUT}/maturity_proto.png", sheet.size)


if __name__ == "__main__":
    main()
