"""Throwaway: the ear takes the skin tone, so check it well outside the default range."""
import sys
sys.path.insert(0, "src")
from dataclasses import replace
import cairosvg
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

C._hair_mass = lambda sk, p: ""
C._hair_front = lambda sk, p: ""
C._hair_defs = lambda sk, p: ""

PALETTES = [("very dark", "#3a2418"), ("olive", "#8f9c4a"), ("near white", "#fbf4ef")]
tiles = []
for label, skin in PALETTES:
    for build in ("chibi", "realistic"):
        p = replace(PRESETS["satoko"], skin_tone=skin)
        sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
        cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/ear/tmp.png")
        im = Image.open("out/ear/tmp.png").convert("RGB")
        w, h = im.size
        frac = 0.46 if build == "chibi" else 0.24
        im = im.crop((int(w * 0.20), 0, int(w * 0.80), int(h * frac)))
        z = max(1, int(430 / im.width))
        tiles.append(im.resize((im.width * z, im.height * z), Image.LANCZOS))
W = sum(t.width for t in tiles); H = max(t.height for t in tiles)
s = Image.new("RGB", (W, H), "white"); x = 0
for t in tiles:
    s.paste(t, (x, 0)); x += t.width
s.save("out/ear/loud.png")
print("wrote out/ear/loud.png", s.size)
