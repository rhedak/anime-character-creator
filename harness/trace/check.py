"""Draw the raw measured profile back onto the reference. If this does not lie
on the hair's edge, the measurement is wrong and no amount of mark-picking
will help."""
import math, sys
sys.path.insert(0, "out/trace")
import numpy as np
from PIL import Image, ImageDraw
from trace import REF, REF_CX, REF_CY, REF_R

a = np.asarray(Image.open(REF).convert("RGB")).astype(int)
ink = a.sum(2) < 700

def radius_at(deg, rmax=2.0, step=0.002):
    th = math.radians(deg)
    last, r = None, 0.30
    while r < rmax:
        x = int(round(REF_CX + math.sin(th) * REF_R * r))
        y = int(round(REF_CY - math.cos(th) * REF_R * r))
        if 0 <= y < ink.shape[0] and 0 <= x < ink.shape[1] and ink[y, x]:
            last = r
        r += step
    return last

BOX = (250, 20, 630, 320); Z = 3
im = Image.open(REF).convert("RGB").crop(BOX)
im = im.resize((im.width*Z, im.height*Z), Image.LANCZOS)
d = ImageDraw.Draw(im)
cx, cy, r = (REF_CX-BOX[0])*Z, (REF_CY-BOX[1])*Z, REF_R*Z
pts = []
for deg in range(-140, 141):
    rad = radius_at(deg)
    if rad:
        th = math.radians(deg)
        pts.append((cx + math.sin(th)*r*rad, cy - math.cos(th)*r*rad))
d.line(pts, fill=(255, 0, 255), width=3)
im.save("out/trace/check.png"); print("wrote out/trace/check.png", im.size)
