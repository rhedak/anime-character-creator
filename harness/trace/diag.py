import sys
sys.path.insert(0, "src")
from dataclasses import replace
import cairosvg
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

base = replace(PRESETS["satoshi"], hairstyle="short_crop")
sk = build_skeleton(heads=BUILDS["realistic"], frame=base.frame)

VARIANTS = [
    ("as is", base, False),
    ("one tone", replace(base, hair_tip_color=base.hair_color), False),
    ("mass only", base, True),
]
tiles = []
for label, p, mass_only in VARIANTS:
    front = C._hair_front
    strands = None
    if mass_only:
        C._hair_front = lambda sk, p: ""
    cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_d.png",
                     output_width=int(sk.canvas_w * 4), output_height=int(sk.canvas_h * 4))
    C._hair_front = front
    im = Image.open("out/trace/_d.png").convert("RGB")
    cx, cy, r = sk.head_cx * 4, sk.head_cy * 4, sk.head_r * 4
    t = im.crop((int(cx - r * 1.9), int(cy - r * 1.6), int(cx + r * 0.1), int(cy + r * 0.3)))
    tiles.append(t)
    print(label)
W = sum(t.width for t in tiles) + 16
H = max(t.height for t in tiles)
s = Image.new("RGB", (W, H), "red")
x = 0
for t in tiles:
    s.paste(t, (x, 0)); x += t.width + 8
s.save("out/trace/diag.png")
print("wrote out/trace/diag.png  as is | one tone | mass only")
