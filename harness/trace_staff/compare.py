"""Reference vs our render, same head-radius window, same scale, side by side."""

import sys

from PIL import Image

from anime_character_creator.character import hat_hair_margin
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

REF = "/Users/henrik/git/time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OUT = "out/trace_staff"
OX, OY, SCALE = 650.0, 481.0, 173.7
name = sys.argv[1]
build = sys.argv[2] if len(sys.argv) > 2 else "chibi"
X0, X1, Y0, Y1 = -3.0, 1.6, -2.9, 6.1
PX = 70  # output px per head radius

p = PRESETS["katherina"]
sk = build_skeleton(heads=BUILDS[build], frame=p.frame, min_hair_margin=hat_hair_margin(p))
ours = Image.open(f"{OUT}/{name}.png").convert("RGB")
k = ours.width / sk.canvas_w


def crop(im, ox, oy, s):
    box = (ox + X0 * s, oy + Y0 * s, ox + X1 * s, oy + Y1 * s)
    return im.crop(tuple(round(v) for v in box)).resize(
        (round((X1 - X0) * PX), round((Y1 - Y0) * PX))
    )


a = crop(Image.open(REF).convert("RGB"), OX, OY, SCALE)
b = crop(ours, sk.head_cx * k, sk.head_cy * k, sk.head_r * k)
c = Image.new("RGB", (a.width * 2 + 10, a.height), "white")
c.paste(a, (0, 0))
c.paste(b, (a.width + 10, 0))
c.save(f"{OUT}/cmp_{name}.png")
print(f"{OUT}/cmp_{name}.png")
