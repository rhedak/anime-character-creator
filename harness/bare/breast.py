"""Step 4b of `docs/bare-body-plan.md`: the bare breast as a shape of its own.

The bust as built for cloth is the torso's side bent outward and brought back
to it in an S (`_bust_shape`): right for a garment, which is the silhouette,
but bare it dents where the S returns and leaves the armpit at a point (the
owner's question, 2026-09-25). Bare, a breast is a round form lying on the
chest and overlapping the side, so here each is its own shape, drawn over the
torso and, at the chibi, over the arms: the lower part of an ellipse, closed
by a chord inside the chest.

Sized from the anchors the bust already has, nothing new:

- widest at the fullest point (`sk.bust_y`), reaching `bust_reach` past the
  body's plain side there, which is where the bent outline's peak was;
- its inner edge `GAP` of the way from the sternum to that side;
- its drop below the widest point is the fold's (`_under_bust_y`, which is
  `bust_reach * _BUST_DROP`), times `depth`: the sweep;
- above the widest point the outer side rises toward the armpit, the outline
  starting at `TOP` degrees, where it leaves the chest, and fading in there;
  the upper slope is chest and has no line. At -55 the fade-in curled into a
  hook against the armpit's corner; -40 still touched it; -28 comes out just
  below it (`out/bare/breast_top.png`).

The outline runs round the outside and the bottom and up the inner side to
`STOP` degrees, tapering toward the sternum. Where it crosses the arm's inner
edge, the edge stops at it (the fill covers the rest), the usual way to draw
one form overlapping another.

Stands in for `_bust_over_arms` (which drew the garments' lobe) and
`_bust_lines` in the mannequin view; nothing in `src/` changes until a depth
is chosen. Chibi only. Writes `out/bare/breast.png`: the current shape, then
a row per depth, a column per adult woman.
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

WOMEN = ("satoko", "chiyo", "keiko", "krista", "reika", "elara")
COLOR_FIELDS = [
    f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name != "boot_color"
]
SCALE = 4
GAP = 0.15
TOP = -28.0
STOP = 170.0
DEPTHS = (0.8, 1.0, 1.25, 1.5)
# When the outline starts at the armpit instead of fading in below it (the
# owner, on the sweep: the stub of the arm's inner edge and the fade-in tail sat
# side by side there, unjoined), it joins the ellipse at its widest point,
# 0 degrees. Joined at -20 the ellipse there lay inside the armpit, and the
# curve went in and back out: a wiggle under the armpit.
JOIN = 0.0


def breasts(depth_k: float, top: float = TOP, joined: bool = False):
    def draw(sk: c.Skeleton, p: c.CharacterParams, chest: str = "") -> str:
        body = c._bust_shape(sk, inset=c._body_inset(sk, p))
        if body is None:
            return ""
        cx, sw, reach = sk.head_cx, c._stroke_w(sk), sk.bust_reach
        yp = body.peak[1]
        x_out = body.peak[0]
        x_in = (x_out - reach) * GAP
        xc, rx = (x_out + x_in) / 2, (x_out - x_in) / 2
        ry_down = (c._under_bust_y(sk, yp) - yp) * depth_k
        ry_up = yp - body.armpit[1]
        a0, a1 = math.radians(JOIN if joined else top), math.radians(STOP)
        steps = 48
        spine = []
        if joined:
            # From the armpit, the corner every part meets at, straight down
            # along the arm's inner edge and curving out onto the ellipse at
            # `JOIN`, arriving on its tangent: one line from the arm's top edge
            # round the breast.
            #
            # The start is the arm's own inner top corner, as `_arms` draws it:
            # the shared armpit point sat a few pixels outside it, and the
            # arm's top edge overshot the start there.
            centre_top, top_y, _, _ = c._arm_line(sk)
            ax = centre_top - sk.arm_half_w
            ay = top_y
            if c._sleeve_under_cap(sk, p):
                ay = c._cap_underside_y(sk, ax, c._cap_tip_y(sk))
            jx, jy = xc + rx * math.cos(a0), yp + ry_up * math.sin(a0)
            # Arrives vertical at the widest point, leaving the armpit down and
            # a little out.
            ctrl = (jx, ay + (jy - ay) * 0.5)
            for k in range(12):
                u = k / 12
                spine.append(
                    (
                        (1 - u) ** 2 * ax + 2 * (1 - u) * u * ctrl[0] + u * u * jx,
                        (1 - u) ** 2 * ay + 2 * (1 - u) * u * ctrl[1] + u * u * jy,
                    )
                )
        for k in range(steps + 1):
            th = a0 + (a1 - a0) * k / steps
            ry = ry_down if math.sin(th) >= 0 else ry_up
            spine.append((xc + rx * math.cos(th), yp + ry * math.sin(th)))
        n = len(spine) - 1
        left, right = [], []
        for k, (x, y) in enumerate(spine):
            q0, q1 = spine[max(0, k - 1)], spine[min(n, k + 1)]
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            norm = math.hypot(dx, dy) or 1.0
            t = k / n
            # Fades in where it leaves the chest, full round the outside and
            # the bottom, tapers out toward the sternum.
            f = min(1.0, (1.0 - t) / 0.3) if joined else min(1.0, t / 0.22, (1.0 - t) / 0.3)
            f **= 0.8
            half = sw * 0.5 * f
            nx, ny = -dy / norm * half, dx / norm * half
            left.append((x + nx, y + ny))
            right.append((x - nx, y - ny))
        ring = left + right[::-1]
        parts = []
        for s in (-1, 1):
            fill = "M " + " L ".join(f"{cx + s * x:.1f} {y:.1f}" for x, y in spine) + " Z"
            parts.append(f'<path d="{fill}" fill="{p.skin_tone}" stroke="none" />')
            line = "M " + " L ".join(f"{cx + s * x:.1f} {y:.1f}" for x, y in ring) + " Z"
            parts.append(f'<path d="{line}" fill="{c.OUTLINE}" stroke="none" />')
            if joined:
                x, y = spine[0]
                parts.append(f'<circle cx="{cx + s * x:.1f}" cy="{y:.1f}" r="{sw * 0.5:.2f}" fill="{c.OUTLINE}" />')
        return "".join(parts)

    return draw


def render(name: str, draw) -> Image.Image:
    p = PRESETS[name]
    p = replace(p, outfit=replace(p.outfit, **dict.fromkeys(COLOR_FIELDS)))
    sk = c.skeleton_for(p)
    saved = {n: getattr(c, n) for n in ("_underpants", "_bust_lines", "_bust_over_arms")}
    try:
        c._underpants = lambda *a, **k: ""
        if draw is not None:
            c._bust_lines = lambda *a, **k: ""
            c._bust_over_arms = draw
        svg = c.render_character(p, sk, background="#ffffff")
    finally:
        for n, fn in saved.items():
            setattr(c, n, fn)
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    s, r, cx = SCALE, sk.head_r * SCALE, sk.head_cx * SCALE
    return im.crop((int(cx - 1.05 * r), int(sk.shoulder_y * s - 0.1 * r), int(cx + 1.05 * r), int(sk.waist_y * s + 0.35 * r)))


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    rows = [("current (the bent side, the tunic's fold line)", None)]
    rows += [(f"own shape, depth {d:g}", breasts(d)) for d in DEPTHS]
    tiles = [(label, [render(n, draw) for n in WOMEN]) for label, draw in rows]
    pad, head = 8, 20
    tw, th = tiles[0][1][0].size
    sheet = Image.new("RGB", (pad + len(WOMEN) * (tw + pad), pad + len(tiles) * (th + head + pad)), (200, 200, 200))
    d = ImageDraw.Draw(sheet)
    y = pad
    for label, row in tiles:
        d.text((pad, y + 4), label + "   (" + ", ".join(WOMEN) + ")", fill=(0, 0, 0))
        x = pad
        for t in row:
            sheet.paste(t, (x, y + head))
            x += tw + pad
        y += th + head + pad
    sheet.save("out/bare/breast.png")
    print("out/bare/breast.png", sheet.size)


if __name__ == "__main__":
    main()
