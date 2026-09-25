"""Step 4b of `docs/bare-body-plan.md`: the line under the bust, bare.

`_bust_lines` was tuned to read through a tunic: a fold's hint, tapering to
nothing at both ends, shallow, fading in with the bust. Bare it is the
breast's own lower contour. This sheet puts variants side by side on the
adult women in the mannequin view (nothing worn, underpants stubbed), for the
owner to pick from. Each variant is drawn here, standing in for
`_bust_lines`; nothing in `src/` changes until one is chosen.

The geometry is `_bust_lines`': the lower arc of an ellipse centred under the
breast, its outer rim on the body's side at the fullest point, its lowest
point near the under-bust height. What varies:

- `start`, `stop`: the arc's angles (0 on the outer side at the fullest
  point, 90 at the bottom, 180 on the inner side at the fullest point's
  height);
- `depth`: the arc's drop, as a multiple of the current one;
- `inner`: the inner half-width, as a fraction of the breast's centre offset;
- `taper`: `both` (the current fold, zero at both ends) or `inner` (full
  weight from the outer end, where it joins the silhouette, tapering only
  toward the sternum);
- `weight`: the line's widest, in strokes; `fade` keeps the current fade-in
  with the bust.

Writes `out/bare/bust_line.png`: a row per variant, a column per woman.
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

# (label, start, stop, depth, inner, taper, weight, fade)
VARIANTS = (
    ("1 current (the tunic's fold)", None, None, None, None, None, None, None),
    ("2 full-weight contour, joined at the side", 8, 150, 1.0, 0.6, "inner", 0.9, False),
    ("3 as 2, rounder and deeper", 8, 165, 1.2, 0.85, "inner", 0.9, False),
    ("4 as 3, stopping short of the sternum", 8, 140, 1.2, 0.6, "inner", 0.9, False),
)
# Variants 2 to 4 start the line at the fullest point's height, so the side
# outline and the line are two marks. These continue the side outline instead:
# the arc starts where the body's outline ends its tuck (`_Bust`'s under-bust
# point), so side, tuck and underside read as one outline of the breast.
# (label, depth, inner, stop)
CONTINUED = (
    ("5 continuing the side outline from its tuck", 1.3, 0.7, 160),
    ("6 as 5, deeper and fuller", 1.6, 0.8, 165),
)
SHOW = ("1", "3", "5", "6")


def variant_line(start, stop, depth_k, inner_k, taper, weight, fade):
    def draw(sk: c.Skeleton, p: c.CharacterParams) -> str:
        body = c._bust_shape(sk, inset=c._body_inset(sk, p))
        if body is None:
            return ""
        cx, sw, reach = sk.head_cx, c._stroke_w(sk), sk.bust_reach
        heaviest = sw * weight * (min(1.0, sk.bust / 0.5) if fade else 1.0)
        peak = body.peak
        low_y = peak[1] + (c._under_bust_y(sk, peak[1]) - peak[1]) * 0.85
        centre = (peak[0] - reach) * 0.5
        out_r = peak[0] - centre
        in_r = centre * inner_k + sw
        depth = (low_y - peak[1]) * depth_k
        a0, a1 = math.radians(start), math.radians(stop)
        steps = 32
        spine = []
        for k in range(steps + 1):
            th = a0 + (a1 - a0) * k / steps
            r_x = out_r if math.cos(th) >= 0 else in_r
            spine.append((centre + r_x * math.cos(th), peak[1] + depth * math.sin(th)))
        n = len(spine) - 1
        left, right = [], []
        for k, (x, y) in enumerate(spine):
            q0, q1 = spine[max(0, k - 1)], spine[min(n, k + 1)]
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            norm = math.hypot(dx, dy) or 1.0
            t = k / n
            if taper == "both":
                f = math.sin(math.pi * t) ** 0.7
            else:
                f = min(1.0, (1.0 - t) / 0.4) ** 0.8
            half = heaviest * 0.5 * f
            nx, ny = -dy / norm * half, dx / norm * half
            left.append((x + nx, y + ny))
            right.append((x - nx, y - ny))
        ring = left + right[::-1]
        parts = []
        for s in (-1, 1):
            d = "M " + " L ".join(f"{cx + s * x:.1f} {y:.1f}" for x, y in ring) + " Z"
            parts.append(f'<path d="{d}" fill="{c.OUTLINE}" stroke="none" />')
            if taper == "inner":
                # A round cap at the outer end, where the line meets the side
                # outline at full weight, so the join has no square corner.
                x, y = spine[0]
                parts.append(f'<circle cx="{cx + s * x:.1f}" cy="{y:.1f}" r="{heaviest * 0.5:.2f}" fill="{c.OUTLINE}" />')
        return "".join(parts)

    return draw


def continued_line(depth_k, inner_k, stop):
    def draw(sk: c.Skeleton, p: c.CharacterParams) -> str:
        body = c._bust_shape(sk, inset=c._body_inset(sk, p))
        if body is None:
            return ""
        cx, sw, reach = sk.head_cx, c._stroke_w(sk), sk.bust_reach
        heaviest = sw * 0.9
        peak = body.peak
        under = body.outline[2][1]
        # Centred half way between the sternum and the body's plain side at the
        # fullest point's height, pushed out by half the reach, at that height.
        xc, yc = (peak[0] - reach) * 0.5 + reach * 0.5, peak[1]
        ry = (under[1] - yc) * depth_k
        a0 = math.asin(min(1.0, (under[1] - yc) / ry))
        rx_out = (under[0] - xc) / math.cos(a0)
        rx_in = xc * inner_k
        a1 = math.radians(stop)
        steps = 32
        spine = []
        for k in range(steps + 1):
            th = a0 + (a1 - a0) * k / steps
            r_x = rx_out if math.cos(th) >= 0 else rx_in
            spine.append((xc + r_x * math.cos(th), yc + ry * math.sin(th)))
        n = len(spine) - 1
        left, right = [], []
        for k, (x, y) in enumerate(spine):
            q0, q1 = spine[max(0, k - 1)], spine[min(n, k + 1)]
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            norm = math.hypot(dx, dy) or 1.0
            half = heaviest * 0.5 * min(1.0, (1.0 - k / n) / 0.4) ** 0.8
            nx, ny = -dy / norm * half, dx / norm * half
            left.append((x + nx, y + ny))
            right.append((x - nx, y - ny))
        ring = left + right[::-1]
        parts = []
        for s in (-1, 1):
            d = "M " + " L ".join(f"{cx + s * x:.1f} {y:.1f}" for x, y in ring) + " Z"
            parts.append(f'<path d="{d}" fill="{c.OUTLINE}" stroke="none" />')
            x, y = spine[0]
            parts.append(f'<circle cx="{cx + s * x:.1f}" cy="{y:.1f}" r="{heaviest * 0.5:.2f}" fill="{c.OUTLINE}" />')
        return "".join(parts)

    return draw


def render(name: str, line) -> Image.Image:
    p = PRESETS[name]
    p = replace(p, outfit=replace(p.outfit, **dict.fromkeys(COLOR_FIELDS)))
    sk = c.skeleton_for(p)
    saved = {n: getattr(c, n) for n in ("_underpants", "_bust_lines")}
    try:
        c._underpants = lambda *a, **k: ""
        if line is not None:
            c._bust_lines = line
        svg = c.render_character(p, sk, background="#ffffff")
    finally:
        for n, fn in saved.items():
            setattr(c, n, fn)
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    s, r, cx = SCALE, sk.head_r * SCALE, sk.head_cx * SCALE
    return im.crop((int(cx - 1.05 * r), int(sk.shoulder_y * s - 0.1 * r), int(cx + 1.05 * r), int(sk.waist_y * s + 0.35 * r)))


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    rows = []
    for label, *args in VARIANTS:
        if label.split()[0] in SHOW:
            line = None if args[0] is None else variant_line(*args)
            rows.append((label, [render(n, line) for n in WOMEN]))
    for label, *args in CONTINUED:
        if label.split()[0] in SHOW:
            rows.append((label, [render(n, continued_line(*args)) for n in WOMEN]))
    pad, head = 8, 20
    tw, th = rows[0][1][0].size
    sheet = Image.new("RGB", (pad + len(WOMEN) * (tw + pad), pad + len(rows) * (th + head + pad)), (200, 200, 200))
    d = ImageDraw.Draw(sheet)
    y = pad
    for label, tiles in rows:
        d.text((pad, y + 4), label + "   (" + ", ".join(WOMEN) + ")", fill=(0, 0, 0))
        x = pad
        for t in tiles:
            sheet.paste(t, (x, y + head))
            x += tw + pad
        y += th + head + pad
    sheet.save("out/bare/bust_line.png")
    print("out/bare/bust_line.png", sheet.size)


main()
