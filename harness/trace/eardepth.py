"""The ear at three depths under the traced crop.

Shipped it sits under `_hair_mass`, which hides it. The canon's own depth is over
the head and under the front locks. Over everything is the third option. The
hair is much bigger than it was when this was last looked at, so the answer may
have changed with it.
"""
import sys
sys.path.insert(0, "src")
from dataclasses import replace
import cairosvg
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton


def variant(p, sk, where):
    svg = C.render_character(p, sk)
    ear = C._ears(sk, p)
    if where == "under the hair":
        return svg
    svg = svg.replace("\n  " + ear, "")
    anchor = C._face(sk, p) if where == "over the head" else C._hair_front(sk, p)
    return svg.replace(anchor, anchor + "\n  " + ear)


for build in ("chibi", "realistic"):
    p = replace(PRESETS["satoshi"], hairstyle="short_crop")
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    tiles = []
    for where in ("under the hair", "over the head", "over everything"):
        cairosvg.svg2png(bytestring=variant(p, sk, where).encode(), write_to="out/trace/_e.png")
        im = Image.open("out/trace/_e.png").convert("RGB")
        w, h = im.size
        frac = 0.46 if build == "chibi" else 0.26
        t = im.crop((int(w * 0.10), 0, int(w * 0.90), int(h * frac)))
        tiles.append(t.resize((int(t.width * 470 / t.height), 470), Image.LANCZOS))
    W = sum(t.width for t in tiles) + 24
    s = Image.new("RGB", (W, 470), "white")
    x = 0
    for t in tiles:
        s.paste(t, (x, 0)); x += t.width + 12
    s.save(f"out/trace/ear_{build}.png")
    print(build, ": under the hair | over the head | over everything")
