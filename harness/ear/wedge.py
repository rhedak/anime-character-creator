"""Throwaway: what the ear looks like at the depth the canon draws it.

Superseded, and kept for the measurement rather than the conclusion. When this
was written `_ears` sat under `_hair_mass`, so both cuts hid the ear entirely
and `ref-out/` was unchanged; this rendered the canon's depth to show why that
could not ship, namely that both cuts fill the temple solidly, so what appears
is a wedge of ear through the hair's inner edge rather than an ear. Changed
pixels are marked red.

The ear has since moved: it now sits over `_hair_mass` and under `_head`, which
is the canon's construction, one unbroken face outline with the ear behind it.
So the first paragraph's z-order no longer describes the code. What survives is
the wedge measurement itself, which is why `long_blunt` and `short_layered` are
still down as needing re-authoring.
"""
import sys
sys.path.insert(0, "src")
import cairosvg
import numpy as np
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

_orig = C.render_character
SRC = _orig.__doc__

def over_head(p, sk):
    svg = _orig(p, sk)
    ear = C._ears(sk, p)
    return svg.replace(ear, "").replace(C._face(sk, p), C._face(sk, p) + "\n  " + ear)

tiles = []
for name, build in (("satoko", "chibi"), ("satoshi", "chibi"),
                    ("satoko", "realistic"), ("satoshi", "realistic")):
    p = PRESETS[name]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    cairosvg.svg2png(bytestring=_orig(p, sk).encode(), write_to="out/ear/a.png")
    cairosvg.svg2png(bytestring=over_head(p, sk).encode(), write_to="out/ear/b.png")
    a = np.asarray(Image.open("out/ear/a.png").convert("RGB")).astype(int)
    b = np.asarray(Image.open("out/ear/b.png").convert("RGB")).astype(int)
    d = np.abs(a - b).sum(2) > 8
    print(f"{name}-{build}: {d.sum()} px of ear would show through the hair")
    img = b.copy(); img[d] = [255, 0, 0]
    im = Image.fromarray(img.astype("uint8"))
    ys, xs = np.where(d)
    pad = 34
    box = (max(0, xs.min()-pad), max(0, ys.min()-pad),
           min(im.width, xs.max()+pad), min(im.height, ys.max()+pad))
    t = im.crop(box); z = max(1, int(430 / t.width))
    tiles.append(t.resize((t.width*z, t.height*z), Image.NEAREST))

W = sum(t.width for t in tiles) + 30
H = max(t.height for t in tiles)
s = Image.new("RGB", (W, H), "white"); x = 0
for t in tiles:
    s.paste(t, (x, 0)); x += t.width + 10
s.save("out/ear/wedge.png")
print("wrote out/ear/wedge.png")
