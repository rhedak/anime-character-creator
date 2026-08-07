import sys
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
import cairosvg
from PIL import Image, ImageDraw
from fit import fit_chain, marks
from satoko import locate, outer
from trace import sample
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

_mass, _front, _defs = C._hair_mass, C._hair_front, C._hair_defs
C._hair_mass = lambda sk, p: ""
C._hair_front = lambda sk, p: ""
C._hair_defs = lambda sk, p: ""

at, _ = locate()
prof = outer(at)
traced = fit_chain(prof, marks(prof, 0.055))
p = PRESETS["satoko"]
sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
C._hair_mass, C._hair_front, C._hair_defs = _mass, _front, _defs
current = C.HAIRSTYLES[p.hairstyle].mass(C._hair_fall(sk, p))
C._hair_mass = lambda sk, p: ""
C._hair_front = lambda sk, p: ""
C._hair_defs = lambda sk, p: ""

S = 3
cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_sp.png",
                 output_width=int(sk.canvas_w * S), output_height=int(sk.canvas_h * S))
im = Image.open("out/trace/_sp.png").convert("RGB")
d = ImageDraw.Draw(im)
cx, cy, r = sk.head_cx * S, sk.head_cy * S, sk.head_r * S
for chain, col in ((current, (0, 150, 255)), (traced, (255, 0, 255))):
    pts = [(cx + x * r, cy + y * r) for x, y in sample(*chain, per=24)]
    d.line(pts, fill=col, width=4)
im.crop((int(im.width * 0.06), 0, int(im.width * 0.94), int(im.height * 0.80))).save(
    "out/trace/satoko_port.png"
)
print("wrote out/trace/satoko_port.png  cyan = what she wears, magenta = traced")
