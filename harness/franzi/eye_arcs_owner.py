"""Circles fitted to the owner's marked arcs on the left eye (out/franzi/eye-outline-L.png with the owner's green and cyan lines).

    ./harness/run.sh harness/franzi/eye_arcs_owner.py

The automatic trace of the lid band (eye_arcs.py) was unreliable: the iris highlight, the brow and the hair beyond the wing tip are
all dark. The owner's lines were read as points off the 8x image (crop origin (545, 275), 8x), converted to reference pixels and
a circle fitted to each. Green: the lid's upper edge continuing as the aperture's outer edge on the open side. Cyan: the lid's
lower edge. Writes out/franzi/eye-arcs-owner-L.png and prints the circles.
"""

import json

import numpy as np
from PIL import Image, ImageDraw

Z, OX, OY = 8, 545, 275
green_z = [(140, 350), (210, 262), (300, 205), (450, 165), (560, 190), (630, 245), (668, 320), (650, 450), (610, 540)]
cyan_z = [(262, 475), (222, 380), (255, 310), (330, 245), (420, 215), (520, 228), (600, 265), (665, 315)]
conv = lambda pts: [(OX + x / Z, OY + y / Z) for x, y in pts]


def fit(pts):
    x = np.array([p[0] for p in pts]); y = np.array([p[1] for p in pts])
    c = np.linalg.lstsq(np.stack([x, y, np.ones_like(x)], 1), -(x**2 + y**2), rcond=None)[0]
    cx, cy = -c[0] / 2, -c[1] / 2
    r = float(np.sqrt(cx**2 + cy**2 - c[2]))
    return cx, cy, r, float(np.sqrt(np.mean((np.hypot(x - cx, y - cy) - r) ** 2)))


g, c = conv(green_z), conv(cyan_z)
fg, fc = fit(g), fit(c)
print("green circle (ref px) cx,cy,r,rms", [round(v, 1) for v in fg])
print("cyan  circle (ref px) cx,cy,r,rms", [round(v, 1) for v in fc])
json.dump({"green": {"pts": g, "circle": fg}, "cyan": {"pts": c, "circle": fc}}, open("out/franzi/eye-arcs-owner-L.json", "w"))
im = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
bg = Image.new("RGBA", im.size, "white"); bg.alpha_composite(im)
img = bg.convert("RGB").crop((OX, OY, OX + 100, OY + 90)).resize((100 * Z, 90 * Z), Image.LANCZOS)
d = ImageDraw.Draw(img)
for (cx, cy, r, _), pts, col in ((fg, g, (0, 200, 0)), (fc, c, (0, 220, 255))):
    ref = np.arctan2(np.mean([p[1] - cy for p in pts]), np.mean([p[0] - cx for p in pts]))
    ang = [(np.arctan2(p[1] - cy, p[0] - cx) - ref + np.pi) % (2 * np.pi) - np.pi + ref for p in pts]
    a0, a1 = min(ang), max(ang)
    t = np.linspace(a0, a1, 80)
    d.line([((cx + r * np.cos(u) - OX) * Z, (cy + r * np.sin(u) - OY) * Z) for u in t], fill=col, width=3)
img.save("out/franzi/eye-arcs-owner-L.png")
