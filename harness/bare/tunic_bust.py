"""T1 of `docs/tunic-bust-plan.md`: variants of the clothed bust that agree
with the bare one, for the owner to pick from.

Six adult women, the tunic on and every other garment off, chest only, same
scale. The bare row first, for reference, then:

- **a** the tunic as it is (the shallow fold, `_bust_lines`);
- **b** the line under the bust taken from the bare ellipse
  (`_bare_breast_spine`'s geometry): from the tunic's side at the fullest
  point round the bottom and up the inner side, at the bare depth; tapered at
  both ends, as a fold in cloth is, since the silhouette carries the outer
  edge;
- **c** as b at 0.85 of the bare depth, cloth bridging the fold a little;
- **d** b plus the silhouette: the tunic's side from the armpit to the widest
  point on the bare outline's curve (arriving vertical there), then the drape
  as now. Done by wrapping `_bust_shape(drape=True)`, so the tunic, the lobe
  over the arm (`_bust_over_arms`) and the traced cuts all follow it.

Nothing in `src/` changes. Writes `out/bare/tunic_bust.png`.
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
KEEP = ("tunic_color", "boot_color", "underwear_color", "skirt_color")
OFF = [f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name not in KEEP]
SCALE = 4


def ellipse_line(depth_k: float):
    """The bare ellipse's lower arc as a tapered fold on the tunic."""

    def draw(sk: c.Skeleton, p: c.CharacterParams) -> str:
        if p.outfit.tunic_color is None:
            return c._bare_breasts(sk, p)
        body = c._bust_shape(sk)
        if body is None:
            return ""
        cx, sw, reach = sk.head_cx, c._stroke_w(sk), sk.bust_reach
        x_out, yp = body.peak
        x_in = (x_out - reach) * c._BREAST_GAP
        xc, rx = (x_out + x_in) / 2, (x_out - x_in) / 2
        ry = (c._under_bust_y(sk, yp) - yp) * c._BREAST_DEPTH * depth_k
        heaviest = sw * 0.95
        stop, steps = math.radians(c._BREAST_STOP), 40
        spine = [(xc + rx * math.cos(th), yp + ry * math.sin(th)) for th in (stop * k / steps for k in range(steps + 1))]
        n = len(spine) - 1
        left, right = [], []
        for k, (x, y) in enumerate(spine):
            q0, q1 = spine[max(0, k - 1)], spine[min(n, k + 1)]
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            norm = math.hypot(dx, dy) or 1.0
            t = k / n
            half = heaviest * 0.5 * min(1.0, t / 0.18, (1.0 - t) / 0.3) ** 0.8
            nx, ny = -dy / norm * half, dx / norm * half
            left.append((x + nx, y + ny))
            right.append((x - nx, y - ny))
        ring = left + right[::-1]
        return "".join(
            '<path d="M ' + " L ".join(f"{cx + s * x:.1f} {y:.1f}" for x, y in ring) + f' Z" fill="{c.OUTLINE}" />'
            for s in (-1, 1)
        )

    return draw


def bare_side(shape):
    """`_bust_shape` with the drape's side above the widest point on the bare
    outline's curve: from the armpit, arriving vertical at the widest point."""

    def wrapped(sk: c.Skeleton, inset: float = 0.0, drape: bool = False):
        b = shape(sk, inset, drape)
        if b is None or not drape:
            return b
        (ax, ay), (px, py) = b.armpit, b.peak
        first = ((px, ay + (py - ay) * 0.5), b.peak)
        return dataclasses.replace(b, outline=(first, *b.outline[1:]))

    return wrapped


VARIANTS = (
    ("bare, for reference", None, False, True),
    ("a  the tunic as it is", None, False, False),
    ("b  line from the bare ellipse, bare depth", 1.0, False, False),
    ("c  as b, 0.85 of the bare depth", 0.85, False, False),
    ("d  b plus the side on the bare outline's curve", 1.0, True, False),
)


def crop(name: str, depth_k, side: bool, bare: bool) -> Image.Image:
    p = PRESETS[name]
    p = replace(p, outfit=replace(p.outfit, **dict.fromkeys(OFF)))
    if bare:
        p = replace(p, outfit=replace(p.outfit, tunic_color=None))
    sk = c.skeleton_for(p)
    saved = {n: getattr(c, n) for n in ("_bust_lines", "_bust_shape")}
    try:
        if depth_k is not None:
            c._bust_lines = ellipse_line(depth_k)
        if side:
            c._bust_shape = bare_side(saved["_bust_shape"])
        svg = c.render_character(p, sk, background="#ffffff")
    finally:
        for n, fn in saved.items():
            setattr(c, n, fn)
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    s, r, cx = SCALE, sk.head_r * SCALE, sk.head_cx * SCALE
    return im.crop((int(cx - 1.05 * r), int(sk.shoulder_y * s - 0.1 * r), int(cx + 1.05 * r), int(sk.waist_y * s + 0.3 * r)))


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    rows = [(label, [crop(n, dk, sd, br) for n in WOMEN]) for label, dk, sd, br in VARIANTS]
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
    sheet.save("out/bare/tunic_bust.png")
    print("out/bare/tunic_bust.png", sheet.size)


if __name__ == "__main__":
    main()
