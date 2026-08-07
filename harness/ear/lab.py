"""Throwaway: ear variants with the hair suppressed, so the ear can be judged."""
import sys
sys.path.insert(0, "src")
import cairosvg
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

C._hair_mass = lambda sk, p: ""
C._hair_front = lambda sk, p: ""
C._hair_defs = lambda sk, p: ""

VARIANTS = [
    ("out .12", dict(_EAR_OUT=0.12)),
    ("out .17", dict(_EAR_OUT=0.17)),
    ("out .22", dict(_EAR_OUT=0.22)),
    ("out .26", dict(_EAR_OUT=0.26)),
]

for build in ("chibi", "realistic"):
    tiles = []
    for label, over in VARIANTS:
        keep = {k: getattr(C, k) for k in over}
        for k, v in over.items():
            setattr(C, k, v)
        p = PRESETS["satoshi"]
        sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
        png = f"out/ear/tmp.png"
        cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to=png)
        im = Image.open(png).convert("RGB")
        w, h = im.size
        im = im.crop((int(w * 0.16), 0, int(w * 0.84), int(h * 0.46)))
        z = max(1, int(700 / im.width))
        tiles.append((label, im.resize((im.width * z, im.height * z), Image.LANCZOS)))
        for k, v in keep.items():
            setattr(C, k, v)
    W = sum(t.width for _, t in tiles)
    H = max(t.height for _, t in tiles)
    strip = Image.new("RGB", (W, H), "white")
    x = 0
    for label, t in tiles:
        strip.paste(t, (x, 0)); x += t.width
    strip.save(f"out/ear/vary_{build}.png")
    print("wrote", build, [lbl for lbl, _ in tiles])
