"""D4c of `docs/detail-plan.md`: a hint of fingers.

The hand is a mitten with a thumb bump (`_hand`), the same shape hanging at the
side and gripping Katherina's staff (drawn under it). Research for this step,
`docs/detail-inventory/hands-research.md`: chibi and distant figures keep the
thumb and drop creases and nails first; a grip reads as stacked curves, one per
finger, down the pole, with the thumb as the anchor. The levels here are
drawn as interior lines over today's silhouette, at `_interior_w`:

- **0** today;
- **1** relaxed: a thumb crease separating the thumb from the palm; gripping:
  the thumb crease and two finger rolls across the fist;
- **2** relaxed: the thumb crease and two short finger lines at the tips;
  gripping: the thumb crease and three finger rolls;
- **3** (a second round: level 2's tip lines read as a paw) relaxed: the
  thumb crease, a fold where the fingers curl under, and one short separation
  below it; gripping: as level 2.

An SVG is drawn once and shown at every size, so it cannot drop lines when
small; the study judges each level at 4x and at the smallest size a chapter
insert shows a figure (head radius about 21 px), 1x and 2x.
Writes `out/detail/hand_study.png`.
"""

import io
import os

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
HAND = c._hand
LEVEL = {"n": 0}


def hand(sk, p, cx, wrist_y, w_wrist, side):
    out = HAND(sk, p, cx, wrist_y, w_wrist, side)
    n = LEVEL["n"]
    if n == 0:
        return out
    hw = w_wrist * 1.02
    L = c._hand_length(sk)
    tip = hw * (1.0 - 0.32 * sk.build)
    w = c._interior_w(c._stroke_w(sk), 0.9)

    def x(o):
        return cx + side * o

    def line(d):
        return f'<path d="{d}" fill="none" stroke="{c.OUTLINE}" stroke-width="{w:.2f}" stroke-linecap="round" />'

    parts = [out]
    # The thumb crease: from where the thumb leaves the palm, up and in.
    parts.append(
        line(
            f"M {x(-hw * 0.84):.1f} {wrist_y + L * 0.60:.1f} "
            f"Q {x(-hw * 0.55):.1f} {wrist_y + L * 0.52:.1f} {x(-hw * 0.42):.1f} {wrist_y + L * 0.34:.1f}"
        )
    )
    grip = side == -1 and p.outfit.staff_color is not None
    if grip:
        rolls = (0.50, 0.72) if n == 1 else (0.42, 0.62, 0.82)
        if n == 3:
            rolls = (0.42, 0.62, 0.82)
        for f in rolls:
            y = wrist_y + L * f
            parts.append(
                line(
                    f"M {x(hw * 1.02):.1f} {y:.1f} Q {x(hw * 0.55):.1f} {y + L * 0.05:.1f} {x(hw * 0.05):.1f} {y:.1f}"
                )
            )
    elif n == 3:
        # The fingers curling under: one fold across the hand from the back of
        # the hand's edge down toward the thumb, and one short separation below.
        parts.append(
            line(
                f"M {x(hw * 1.04):.1f} {wrist_y + L * 0.50:.1f} "
                f"Q {x(hw * 0.35):.1f} {wrist_y + L * 0.62:.1f} {x(-hw * 0.30):.1f} {wrist_y + L * 0.74:.1f}"
            )
        )
        parts.append(
            line(
                f"M {x(hw * 0.28):.1f} {wrist_y + L * 0.64:.1f} "
                f"Q {x(hw * 0.26):.1f} {wrist_y + L * 0.82:.1f} {x(hw * 0.22):.1f} {wrist_y + L * 0.98:.1f}"
            )
        )
    elif n == 2:
        for fx in (-0.18, 0.30):
            parts.append(
                line(
                    f"M {x(tip * fx):.1f} {wrist_y + L * 1.03:.1f} "
                    f"Q {x(tip * (fx + 0.04)):.1f} {wrist_y + L * 0.90:.1f} {x(tip * (fx + 0.02)):.1f} {wrist_y + L * 0.78:.1f}"
                )
            )
    return "".join(parts)


def crop(p, scale, s, box):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB")
    ux, uy = c._hand_centre(sk, p, s)
    hx, hy = (sk.head_cx + ux * sk.head_r) * scale, (sk.head_cy + uy * sk.head_r) * scale
    r = sk.head_r * scale
    return im.crop((int(hx - box * r), int(hy - box * r), int(hx + box * r), int(hy + box * r)))


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = (("katherina", -1, "grip"), ("katherina", 1, "relaxed"), ("krista", 1, "relaxed"), ("gero", 1, "relaxed"))
    rows = []
    c._hand = hand
    try:
        for n in (0, 1, 2, 3):
            LEVEL["n"] = n
            row = []
            for name, s, kind in cases:
                p = PRESETS[name]
                big = crop(p, 4, s, 0.6)
                sk = c.skeleton_for(p)
                k = 21.0 / sk.head_r
                small = [crop(p, k * d * 4, s, 1.2) for d in (1, 2)]
                small = [im.resize((im.width // 4, im.height // 4), Image.LANCZOS) for im in small]
                small = [im.resize((im.width * 3 // d, im.height * 3 // d), Image.NEAREST) for im, d in zip(small, (1, 2))]
                tile = Image.new("RGB", (big.width + small[0].width + small[1].width + 8, big.height), (255, 255, 255))
                tile.paste(big, (0, 0))
                tile.paste(small[0], (big.width + 4, 0))
                tile.paste(small[1], (big.width + small[0].width + 8, 0))
                ImageDraw.Draw(tile).text((3, 3), f"level {n}: {name} {kind} (4x; insert 1x, 2x shown 3x)", fill=(200, 0, 0))
                row.append(tile)
            rows.append(row)
    finally:
        c._hand = HAND
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(rows[0]) * (tw + 4), len(rows) * (th + 6)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 4), j * (th + 6)))
    sheet.save(f"{OUT}/hand_study.png")
    print(f"{OUT}/hand_study.png", sheet.size)


if __name__ == "__main__":
    main()
