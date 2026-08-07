import sys
sys.path.insert(0, "src")
from dataclasses import replace
import cairosvg
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

p = replace(PRESETS["satoshi"], hairstyle="short_crop")
sk = build_skeleton(heads=BUILDS["realistic"], frame=p.frame)
cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_z.png",
                 output_width=int(sk.canvas_w * 4), output_height=int(sk.canvas_h * 4))
im = Image.open("out/trace/_z.png").convert("RGB")
# upper left quadrant of the head
cx, cy, r = sk.head_cx * 4, sk.head_cy * 4, sk.head_r * 4
box = (int(cx - r * 2.0), int(cy - r * 2.0), int(cx + r * 0.2), int(cy + r * 0.4))
t = im.crop(box)
t = t.resize((t.width * 2, t.height * 2), Image.LANCZOS)
t.save("out/trace/zoomcheck.png")
print("wrote", t.size)
