"""What moving the ear over the head does to the two cuts that still ship."""
import sys
sys.path.insert(0, "src")
import cairosvg
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

tiles = []
for name, build in (("satoko", "chibi"), ("satoshi", "chibi"),
                    ("satoko", "realistic"), ("satoshi", "realistic")):
    p = PRESETS[name]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    svg = C.render_character(p, sk)
    ear = C._ears(sk, p)
    face = C._face(sk, p)
    over = svg.replace("\n  " + ear, "").replace(face, face + "\n  " + ear)
    for s in (svg, over):
        cairosvg.svg2png(bytestring=s.encode(), write_to="out/trace/_o.png")
        im = Image.open("out/trace/_o.png").convert("RGB")
        w, h = im.size
        frac = 0.42 if build == "chibi" else 0.24
        t = im.crop((int(w * 0.16), 0, int(w * 0.84), int(h * frac)))
        tiles.append(t.resize((int(t.width * 300 / t.height), 300), Image.LANCZOS))
W = sum(t.width for t in tiles) + 8 * len(tiles)
s = Image.new("RGB", (W, 300), "white")
x = 0
for i, t in enumerate(tiles):
    s.paste(t, (x, 0)); x += t.width + (4 if i % 2 == 0 else 22)
s.save("out/trace/oldcuts.png")
print("wrote out/trace/oldcuts.png  pairs: shipped, ear over the head")
