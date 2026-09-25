"""Step 6 of `docs/bare-body-plan.md`: the minimum male torso, a proposal.

With the tunic off a man is the women's body at bust 0: at the chibi the
silhouette is identical, since `frame` (shoulder against hip) rides the build
and comes to well under a percent there, and the long-torso profile sets the
waist and hip widths itself. So the lever is line work, as it was for the bust
at the chibi: two soft arcs under the pectorals, tapering at both ends, a gap
at the sternum. Drawn here standing in beside `_underwear_top` (which draws
nothing without a bust), so nothing in `src/` changes until it is chosen.

The proposed knob is `chest`, 0 to 1, a trait beside `bust` rather than a sex
flag: how much chest definition shows bare. Drawn only with no bust, since the
breasts replace it. What varies here:

- `amount`: the knob, scaling the arcs' depth and weight;
- `navel`: a small dot, the one other mark a bare torso reads by.

The men in the base-layer view (underwear, barefoot), chibi. Writes
`out/bare/male_torso.png`: a row per variant, a column per man.
"""

import dataclasses
import io
import math
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

MEN = ("gero", "satoshi", "tomohiro", "daizen", "haruto", "reinhard", "tenno", "viktor")
OFF = [f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name != "underwear_color"]
SCALE = 3
# (label, amount, navel)
VARIANTS = (
    ("current: no chest lines", 0.0, False),
    ("chest 0.5", 0.5, False),
    ("chest 1.0", 1.0, False),
    ("chest 1.0 with a navel", 1.0, True),
)


def chest_lines(amount: float, navel: bool):
    top = c._underwear_top

    def draw(sk: c.Skeleton, p: c.CharacterParams) -> str:
        out = top(sk, p)
        if p.outfit.tunic_color is not None or sk.bust > 0 or amount <= 0:
            return out
        cx, sw = sk.head_cx, c._stroke_w(sk)
        side = c._torso_at_armpit(sk)
        run = sk.waist_y - sk.shoulder_y
        # The lower border of the chest at about the nipple line, the canon's
        # half way from the shoulder line to the waist.
        fold_y = sk.shoulder_y + run * 0.50
        depth = run * 0.07 * (0.6 + 0.4 * amount)
        x_out, x_in = side * 0.92, side * 0.10
        xc, rx = (x_out + x_in) / 2, (x_out - x_in) / 2
        yc = fold_y - depth
        heaviest = sw * 0.8 * (0.5 + 0.5 * amount)
        a0, a1, steps = math.radians(15), math.radians(165), 28
        spine = [
            (xc + rx * math.cos(a0 + (a1 - a0) * k / steps), yc + depth * math.sin(a0 + (a1 - a0) * k / steps))
            for k in range(steps + 1)
        ]
        n = len(spine) - 1
        left, right = [], []
        for k, (x, y) in enumerate(spine):
            q0, q1 = spine[max(0, k - 1)], spine[min(n, k + 1)]
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            norm = math.hypot(dx, dy) or 1.0
            half = heaviest * 0.5 * math.sin(math.pi * k / n) ** 0.7
            nx, ny = -dy / norm * half, dx / norm * half
            left.append((x + nx, y + ny))
            right.append((x - nx, y - ny))
        ring = left + right[::-1]
        for s in (-1, 1):
            d = "M " + " L ".join(f"{cx + s * x:.1f} {y:.1f}" for x, y in ring) + " Z"
            out += f'<path d="{d}" fill="{c.OUTLINE}" stroke="none" />'
        if navel:
            ny_ = sk.waist_y + (sk.hip_y - sk.waist_y) * 0.15
            out += (
                f'<ellipse cx="{cx:.1f}" cy="{ny_:.1f}" rx="{sw * 0.45:.2f}" ry="{sw * 0.7:.2f}" '
                f'fill="{c.OUTLINE}" />'
            )
        return out

    return draw


def render(name: str, amount: float, navel: bool) -> Image.Image:
    p = PRESETS[name]
    p = replace(p, outfit=replace(p.outfit, **dict.fromkeys(OFF)))
    sk = c.skeleton_for(p)
    saved = c._underwear_top
    try:
        c._underwear_top = chest_lines(amount, navel)
        svg = c.render_character(p, sk, background="#ffffff")
    finally:
        c._underwear_top = saved
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    s, r, cx = SCALE, sk.head_r * SCALE, sk.head_cx * SCALE
    return im.crop((int(cx - 1.2 * r), int(sk.head_cy * s), int(cx + 1.2 * r), int(sk.hip_y * s + 0.8 * r)))


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    rows = [(label, [render(n, a, nv) for n in MEN]) for label, a, nv in VARIANTS]
    pad, head = 8, 20
    tw, th = rows[0][1][0].size
    sheet = Image.new("RGB", (pad + len(MEN) * (tw + pad), pad + len(rows) * (th + head + pad)), (200, 200, 200))
    d = ImageDraw.Draw(sheet)
    y = pad
    for label, tiles in rows:
        d.text((pad, y + 4), label + "   (" + ", ".join(MEN) + ")", fill=(0, 0, 0))
        x = pad
        for t in tiles:
            sheet.paste(t, (x, y + head))
            x += tw + pad
        y += th + head + pad
    sheet.save("out/bare/male_torso.png")
    print("out/bare/male_torso.png", sheet.size)


if __name__ == "__main__":
    main()
