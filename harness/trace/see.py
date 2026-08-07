"""The traced crop at both builds, beside the canon and beside what ships today."""
import sys
sys.path.insert(0, "src")
from dataclasses import replace
import cairosvg
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

def render(style, build):
    p = replace(PRESETS["satoshi"], hairstyle=style)
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_s.png")
    im = Image.open("out/trace/_s.png").convert("RGB")
    w, h = im.size
    frac = 0.46 if build == "chibi" else 0.26
    return im.crop((int(w * 0.10), 0, int(w * 0.90), int(h * frac)))

def fit(im, H):
    return im.resize((int(im.width * H / im.height), H), Image.LANCZOS)

for build, refimg, box in (("chibi", "ref/satoshi-chibi.jpg", (150, 40, 730, 570)),
                           ("realistic", "ref/satoshi-real.jpg", (255, 20, 620, 300))):
    ref = Image.open(refimg).convert("RGB").crop(box)
    tiles = [fit(ref, 460), fit(render("short_crop", build), 460),
             fit(render("short_layered", build), 460)]
    W = sum(t.width for t in tiles) + 24
    s = Image.new("RGB", (W, 460), "white")
    x = 0
    for t in tiles:
        s.paste(t, (x, 0)); x += t.width + 12
    s.save(f"out/trace/see_{build}.png")
    print("wrote", build, "  canon | traced crop | what ships today")
