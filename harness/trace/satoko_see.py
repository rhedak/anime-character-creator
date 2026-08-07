import sys
sys.path.insert(0, "src")
from dataclasses import replace
import cairosvg
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

def render(style, build):
    p = replace(PRESETS["satoko"], hairstyle=style)
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_sk.png")
    im = Image.open("out/trace/_sk.png").convert("RGB")
    w, h = im.size
    frac = 0.70 if build == "chibi" else 0.36
    return im.crop((int(w * 0.06), 0, int(w * 0.94), int(h * frac)))

def fit(im, H):
    return im.resize((int(im.width * H / im.height), H), Image.LANCZOS)

for build, box in (("chibi", (150, 60, 760, 700)), ("realistic", (250, 20, 640, 420))):
    ref = Image.open("ref/satoko-chibi.jpg" if build == "chibi" else "ref/satoko-real.jpg")
    tiles = [fit(ref.convert("RGB").crop(box), 520),
             fit(render("long_traced", build), 520),
             fit(render("long_blunt", build), 520)]
    W = sum(t.width for t in tiles) + 24
    s = Image.new("RGB", (W, 520), "white")
    x = 0
    for t in tiles:
        s.paste(t, (x, 0)); x += t.width + 12
    s.save(f"out/trace/satoko_see_{build}.png")
    print(build, ": canon | traced | what she wears")
