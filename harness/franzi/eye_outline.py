"""Our eye aperture (and lid) drawn as plain lines over the reference, 8x. ./harness/run.sh harness/franzi/eye_outline.py

Canvas units map to reference pixels by the body gate's mapping (a head radius is 175.7 reference px less the 8.2 px the head
shift moves it; centre column 668.2, chin row 434). Red: the aperture. Blue: the lid band. Orange: the crease. Green: the lashes (a ring marks each one's base). Writes out/franzi/eye-outline-{L,R}.png.
"""

import json
import subprocess

from PIL import Image, ImageDraw

subprocess.run(["node", "harness/franzi/eye_outline.ts", "out/franzi/eye-outline.json"], check=True)
subprocess.run(["node", "harness/franzi/underwear.ts", "adult_female", "out/franzi/al-meta.svg"], check=True)
meta = json.load(open("out/franzi/al-meta.json"))
o = json.load(open("out/franzi/eye-outline.json"))
sc = 352.0 / (2 * meta["head_r"])  # reference px per canvas unit
CX_REF, CHIN_REF = 668.2, 434.0
chin_c = meta["chin_y"]
cx_c = meta["canvas_w"] / 2


def to_ref(p):
    return (CX_REF + (p[0] - cx_c) * sc, CHIN_REF + (p[1] - chin_c) * sc)


im = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
bg = Image.new("RGBA", im.size, "white")
bg.alpha_composite(im)
bg = bg.convert("RGB")
Z = 12
for name, box, side in (("L", (550, 280, 645, 345), -1), ("R", (685, 275, 780, 340), 1)):
    c = bg.crop(box).resize(((box[2] - box[0]) * Z, (box[3] - box[1]) * Z), Image.LANCZOS)
    d = ImageDraw.Draw(c)
    e = next(x for x in o["eyes"] if x["side"] == side)
    for key, col in (("aperture", (230, 0, 0)), ("lid", (0, 90, 255)), ("crease", (255, 140, 0))):
        pts = [((x - box[0]) * Z, (y - box[1]) * Z) for x, y in map(to_ref, e[key])]
        d.line(pts + ([pts[0]] if key in ('aperture', 'lid') else []), fill=col, width=3)
    # the lashes (their centre lines): bright green, with a dot at each one's base so it can be seen where it attaches
    for lash in e["lashes"]:
        pts = [((x - box[0]) * Z, (y - box[1]) * Z) for x, y in map(to_ref, lash)]
        d.line(pts, fill=(0, 220, 60), width=4)
        d.ellipse((pts[0][0] - 5, pts[0][1] - 5, pts[0][0] + 5, pts[0][1] + 5), outline=(0, 0, 0), width=2)
    c.save(f"out/franzi/eye-outline-{name}.png")
print("wrote out/franzi/eye-outline-L.png and -R.png")
