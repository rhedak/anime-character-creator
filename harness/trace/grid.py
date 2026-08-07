"""A polar grid in head-radius units over the reference, to read points off."""
import math, sys
sys.path.insert(0, "out/trace")
from PIL import Image, ImageDraw, ImageFont
from trace import REF, REF_CX, REF_CY, REF_R

BOX = (250, 10, 640, 330)
Z = 3
im = Image.open(REF).convert("RGB").crop(BOX)
im = im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
d = ImageDraw.Draw(im)
cx, cy, r = (REF_CX - BOX[0]) * Z, (REF_CY - BOX[1]) * Z, REF_R * Z

for rad in (0.6, 0.8, 1.0, 1.2, 1.4, 1.6):
    col = (255, 0, 0) if rad == 1.0 else (0, 170, 255)
    d.ellipse([cx - r*rad, cy - r*rad, cx + r*rad, cy + r*rad], outline=col, width=2 if rad==1.0 else 1)
    d.text((cx + 4, cy - r*rad - 14), f"{rad:.1f}", fill=col)
for deg in range(0, 360, 15):
    a = math.radians(deg)
    x2, y2 = cx + math.sin(a) * r * 1.7, cy - math.cos(a) * r * 1.7
    d.line([(cx, cy), (x2, y2)], fill=(120, 255, 120), width=1)
    d.text((cx + math.sin(a) * r * 1.62 - 8, cy - math.cos(a) * r * 1.62 - 6), str(deg), fill=(0, 130, 0))
im.save("out/trace/grid.png")
print("wrote out/trace/grid.png", im.size)
