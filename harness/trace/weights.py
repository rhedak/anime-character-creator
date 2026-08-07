"""The same trace at three levels, drawn at our real line weight.

The overlays so far were a thin hairline over a 3x reference, which flatters
fine detail. `_stroke_w` is figure-relative, so rendering bigger does not rescue
a feature narrower than the stroke: the ratio is scale-free. This draws the
contour at the true weight and then magnifies the result.
"""
import sys
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
import cairosvg
from PIL import Image, ImageDraw
from fit import fit_chain, marks, profile
from trace import sample
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

C._hair_mass = lambda sk, p: ""
C._hair_front = lambda sk, p: ""
C._hair_defs = lambda sk, p: ""

prof = profile()
rows = []
for build in ("chibi", "realistic"):
    p = PRESETS["satoshi"]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    tiles = []
    for tol in (0.018, 0.065, 0.090):
        ch = fit_chain(prof, marks(prof, tol))
        cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_w.png")
        im = Image.open("out/trace/_w.png").convert("RGB")
        s = im.width / sk.canvas_w
        d = ImageDraw.Draw(im)
        pts = [(sk.head_cx * s + x * sk.head_r * s, sk.head_cy * s + y * sk.head_r * s)
               for x, y in sample(*ch, per=24)]
        d.line(pts, fill=(20, 20, 20), width=max(1, round(C._stroke_w(sk) * s)),
               joint="curve")
        frac = 0.50 if build == "chibi" else 0.28
        t = im.crop((int(im.width * 0.12), 0, int(im.width * 0.88), int(im.height * frac)))
        z = max(1, round(560 / t.width))
        tiles.append(t.resize((t.width * z, t.height * z), Image.LANCZOS))
    W = sum(t.width for t in tiles) + 16
    H = max(t.height for t in tiles)
    row = Image.new("RGB", (W, H), "white")
    x = 0
    for t in tiles:
        row.paste(t, (x, 0)); x += t.width + 8
    rows.append(row)

W = max(r.width for r in rows); H = sum(r.height for r in rows) + 10
out = Image.new("RGB", (W, H), "white")
y = 0
for r in rows:
    out.paste(r, (0, y)); y += r.height + 10
out.save("out/trace/weights.png")
print("wrote out/trace/weights.png", out.size, "  columns: 50 segs, 26 segs, 21 segs")
