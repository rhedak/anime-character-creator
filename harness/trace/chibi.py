"""The same extraction on the canon's chibi, to settle whether a cut's outline
is one shape at both builds or two.

Calibration is the same eye-to-chin fit, with the chibi's own 0.84 r run rather
than the adult's 0.89, since `chin_drop` is zero at build 0. It checks out
independently: the reference's eye half-separation comes to 0.466 head radii
against our house 0.46.
"""
import math, sys
sys.path.insert(0, "out/trace")
import numpy as np
from PIL import Image
from fit import fit_chain, marks, polar

REF = "ref/satoshi-chibi.jpg"
CX, EYE_Y, CHIN_Y = 434.0, 380.0, 528.0
R = (CHIN_Y - EYE_Y) / 0.84
CY = EYE_Y - 0.16 * R

_a = np.asarray(Image.open(REF).convert("RGB")).astype(int)
INK = _a.sum(2) < 700


def radius_at(deg, rmax=2.0, step=0.002):
    th = math.radians(deg)
    last, r = None, 0.30
    while r < rmax:
        x = int(round(CX + math.sin(th) * R * r))
        y = int(round(CY - math.cos(th) * R * r))
        if 0 <= y < INK.shape[0] and 0 <= x < INK.shape[1] and INK[y, x]:
            last = r
        r += step
    return last


prof = [(float(d), radius_at(d)) for d in range(-130, 131)]
prof = [(d, r) for d, r in prof if r is not None and r < 1.7]
print(f"chibi reference: head centre ({CX:.0f}, {CY:.0f}) radius {R:.1f}px")
print(f"{'bearing':>8s} {'chibi ref':>10s}")
for d in range(-130, 131, 10):
    hit = [r for dd, r in prof if dd == d]
    if hit:
        print(f"{d:8d} {hit[0]:10.3f}")
mk = marks(prof, 0.090)
ch = fit_chain(prof, mk)
print(f"\n{len(ch[1])} segments after the same simplification")
top = min(y for _, y in [polar(d, r) for d, r in mk])
wide = max(abs(x) for x, _ in [polar(d, r) for d, r in mk])
print(f"topmost mark y={top:+.3f}   widest mark x={wide:.3f}")


# Draw it back on, the same check the adult trace got. A contour that does not
# lie on the hair means the calibration is wrong and the comparison is worthless.
from PIL import ImageDraw  # noqa: E402
from trace import sample  # noqa: E402

BOX, Z = (120, 20, 760, 620), 2
im = Image.open(REF).convert("RGB").crop(BOX)
im = im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
d = ImageDraw.Draw(im)
cx, cy, r = (CX - BOX[0]) * Z, (CY - BOX[1]) * Z, R * Z
pts = [(cx + x * r, cy + y * r) for x, y in sample(*ch, per=18)]
d.line(pts, fill=(255, 0, 255), width=4)
for rad, col in ((1.0, (255, 0, 0)), (1.30, (0, 170, 255))):
    d.ellipse([cx - r*rad, cy - r*rad, cx + r*rad, cy + r*rad], outline=col, width=3)
im.save("out/trace/chibi_check.png")
print("wrote out/trace/chibi_check.png  (red = skull r=1.0, blue = the adult's crown r=1.30)")
