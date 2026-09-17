"""Render a character with its hair (and hat, staff) switched off, to see what the
hair hides: `bare.py <out.png> [preset] [scale] [x0 x1 y0 y1]` (head radii window).
Diagnostic only: patches the hair parts to draw nothing for this process."""

import dataclasses
import io
import sys

import cairosvg
from PIL import Image

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

for part in ("_hair_mass", "_hair_front", "_hair_tail", "_hair_knot", "_hair_tie", "_hair_defs"):
    setattr(c, part, lambda sk, p: "")
out = sys.argv[1]
name = sys.argv[2] if len(sys.argv) > 2 else "katherina"
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 4
win = [float(v) for v in sys.argv[4:8]] if len(sys.argv) > 7 else None
p = PRESETS[name]
if name != "katherina":
    cuts = dict(collar_cut="pointed", skirt_cut="a_line", coat_cut="open_jacket", sleeve_cut="wide", belt_cut="buckled")
    p = dataclasses.replace(
        p,
        body="tall_chibi",
        outfit=dataclasses.replace(
            p.outfit, apron_color=None, pouch_color=None, underskirt_color=None, collar_color="#c4903c",
            coat_color="#3a4a36", sleeve_long=True, tunic_tucked=True, **cuts,
        ),
    )
p = dataclasses.replace(p, outfit=dataclasses.replace(p.outfit, hat_color=None, staff_color=None))
sk = c.skeleton_for(p)
im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=c.render_character(p, sk, background="white").encode(), scale=scale))).convert("RGB")
if win:
    k = im.width / sk.canvas_w
    x0, x1, y0, y1 = win
    box = (sk.head_cx * k + x0 * sk.head_r * k, sk.head_cy * k + y0 * sk.head_r * k, sk.head_cx * k + x1 * sk.head_r * k, sk.head_cy * k + y1 * sk.head_r * k)
    im = im.crop(tuple(round(v) for v in box))
im.save(out)
