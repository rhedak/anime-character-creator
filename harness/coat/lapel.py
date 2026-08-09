"""Where the coat's lapel rises to meet the neck.

The two panels currently run from a point at the collarbone straight out to the
shoulder, in one line. Nothing in that line touches the neck, so the whole strip
of shoulder next to the neck is bare, and each panel reads as a wedge floating
on the chest rather than a coat draped from the shoulders down. The fix adds a
third point, hugging the side of the neck, between the throat point and the
shoulder point.

Two numbers to find: how far out from the neck the lapel sits, and how high it
climbs. Too close and it reads as painted on the neck; too far and it stops
looking like a collar. Too high and it pokes up into the jaw; too low and the
gap is still there, just smaller.
"""

import io
import pathlib
import sys

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from anime_character_creator import PRESETS, build_skeleton, render_character
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/coat")
OUT.mkdir(parents=True, exist_ok=True)

BASE = C._coat


def make_coat(lapel_x, lapel_y_off):
    def _coat(sk, p):
        if p.outfit.coat_color is None:
            return ""
        cx = sk.head_cx
        color = p.outfit.coat_color
        sw = C._stroke_w(sk)
        sy = sk.shoulder_y
        hem_y = sy + (sk.ankle_y - sy) * max(0.0, min(1.0, p.outfit.coat_length))
        shoulder_w = C._sleeve_half_w(sk) * 0.92
        gap_top = sk.neck_half_w * 0.55
        gap_hem = sk.waist_half_w * 0.52
        out_hem = max(sk.hip_half_w * 1.06, C._skirt_half_w(sk, hem_y) * 0.94)
        waist_y = sk.waist_y
        throat_y = sy + sk.neck_half_w * 0.5
        lapel_px = sk.neck_half_w * lapel_x
        lapel_py = sy - sk.neck_half_w * lapel_y_off
        shoulder_py = sy + (waist_y - sy) * 0.16
        parts = []
        for s in (-1, 1):
            d = (
                f"M {cx + s * gap_top:.1f} {throat_y:.1f} "
                f"L {cx + s * lapel_px:.1f} {lapel_py:.1f} "
                f"L {cx + s * shoulder_w:.1f} {shoulder_py:.1f} "
                f"Q {cx + s * shoulder_w * 1.02:.1f} {waist_y:.1f} "
                f"{cx + s * out_hem:.1f} {hem_y:.1f} "
                f"L {cx + s * gap_hem:.1f} {hem_y:.1f} "
                f"Q {cx + s * gap_top * 1.35:.1f} {waist_y:.1f} "
                f"{cx + s * gap_top:.1f} {throat_y:.1f} Z"
            )
            parts.append(f'<path d="{d}" fill="{color}" stroke="{C.OUTLINE}" stroke-width="{sw:.1f}" />')
        return "".join(parts)

    return _coat


CANDIDATES = [
    ("before", None),
    ("x1.1 y0.6", 1.1, 0.6),
    ("x1.3 y1.0", 1.3, 1.0),
    ("x1.5 y1.4", 1.5, 1.4),
    ("x1.5 y2.0", 1.5, 2.0),
]


def render(cand, size):
    label = cand[0]
    C._coat = BASE if label == "before" else make_coat(cand[1], cand[2])
    p = PRESETS["keiko"]
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=900)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    w, h = im.size
    if size == "head":
        im = im.crop((int(w * 0.10), int(h * 0.18), int(w * 0.90), int(h * 0.60)))
        return im.resize((280, int(280 * im.height / im.width)), Image.LANCZOS)
    im.thumbnail((100, 135), Image.LANCZOS)
    return im


canon = Image.open("ref/keiko.png").convert("RGB")
w, h = canon.size
c = canon.crop((int(w * 0.18), int(h * 0.10), int(w * 0.82), int(h * 0.45)))
tiles = [("canon", c.resize((280, int(280 * c.height / c.width)), Image.LANCZOS))]
for cand in CANDIDATES:
    tiles.append((cand[0], render(cand, "head")))
    tiles.append(("", render(cand, "tile")))
C._coat = BASE

W = sum(t.width for _, t in tiles) + 10 * (len(tiles) + 1)
H = max(t.height for _, t in tiles) + 34
canv = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(canv)
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
x = 10
for label, t in tiles:
    if label:
        d.text((x, 6), label, font=f, fill=(255, 255, 255))
    canv.paste(t, (x, 30))
    x += t.width + 10
canv.save(OUT / "lapel.png")
print("wrote", OUT / "lapel.png", canv.size)
