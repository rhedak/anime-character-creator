"""Overlay each hair piece on the render in its own colour, to see which black
line is which."""
import sys
sys.path.insert(0, "src")
from dataclasses import replace
import cairosvg
from PIL import Image, ImageDraw
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

p = replace(PRESETS["satoshi"], hairstyle="short_crop")
sk = build_skeleton(heads=BUILDS["realistic"], frame=p.frame)
S = 8
cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_q.png",
                 output_width=int(sk.canvas_w*S), output_height=int(sk.canvas_h*S))
im = Image.open("out/trace/_q.png").convert("RGB")
d = ImageDraw.Draw(im)
cx, cy, r = sk.head_cx*S, sk.head_cy*S, sk.head_r*S
fall = C._hair_fall(sk, p)

def walk(start, segs, per=30):
    pts, prev = [start], start
    for ctrl, end in segs:
        for i in range(1, per+1):
            t = i/per
            pts.append(((1-t)**2*prev[0]+2*(1-t)*t*ctrl[0]+t**2*end[0],
                        (1-t)**2*prev[1]+2*(1-t)*t*ctrl[1]+t**2*end[1]))
        prev = end
    return [(cx + x*r, cy + y*r) for x, y in pts]

start, line, back = C._crop_hairline_shape(fall)
d.line(walk(*C._crop_mass_shape(fall)), fill=(255, 0, 255), width=3)      # mass
d.line(walk(start, line), fill=(0, 200, 255), width=3)                    # fringe stroke
d.line(walk(line[-1][1], back), fill=(0, 220, 0), width=3)                # closing edge
box = (int(cx - r*1.9), int(cy - r*1.7), int(cx + r*0.2), int(cy + r*0.2))
im.crop(box).save("out/trace/probe3.png")
print("wrote out/trace/probe3.png  magenta=mass, cyan=fringe stroke, green=closing edge")
