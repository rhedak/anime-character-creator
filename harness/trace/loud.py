"""Throwaway: the promoted cut well outside the blonde palette it was tuned on."""
import sys
sys.path.insert(0, "src")
from dataclasses import replace
import cairosvg
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

PALETTES = [
    ("near black on plum", "#1d1a24", "#7a5f86"),
    ("teal on cream", "#1f6f6a", "#f2efe0"),
    ("one tone red", "#8c2f2f", "#8c2f2f"),
]
tiles = []
for label, hair, tips in PALETTES:
    for build in ("chibi", "realistic"):
        p = replace(PRESETS["satoshi"], hair_color=hair, hair_tip_color=tips)
        sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
        cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_l.png")
        im = Image.open("out/trace/_l.png").convert("RGB")
        w, h = im.size
        frac = 0.46 if build == "chibi" else 0.26
        t = im.crop((int(w * 0.12), 0, int(w * 0.88), int(h * frac)))
        tiles.append(t.resize((int(t.width * 300 / t.height), 300), Image.LANCZOS))
W = sum(t.width for t in tiles) + 8 * len(tiles)
s = Image.new("RGB", (W, 300), "white")
x = 0
for t in tiles:
    s.paste(t, (x, 0)); x += t.width + 8
s.save("out/trace/loud.png")
print("wrote out/trace/loud.png", [p[0] for p in PALETTES])
