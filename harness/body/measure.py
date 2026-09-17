"""Our render's garment landmarks in head radii, next to the reference's.

Renders KATHERINA at scale 4 without the staff (it would merge with the coat on
the viewer's left) and measures each flat fill colour's rows and spans.
"""

import dataclasses
import io
import sys

import cairosvg
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

p = PRESETS["katherina"]
if len(sys.argv) > 1:
    exec(sys.argv[1])  # quick overrides, e.g. p = dataclasses.replace(p, hair_length=0.7)
p = dataclasses.replace(p, outfit=dataclasses.replace(p.outfit, staff_color=None))
sk = c.skeleton_for(p)
K = 4
svg = c.render_character(p, sk, background="#ff00ff")
im = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=K))).convert("RGB")).astype(int)
cx, cy, r = sk.head_cx * K, sk.head_cy * K, sk.head_r * K


def mask(hexc, tol=10):
    col = np.array([int(hexc[i : i + 2], 16) for i in (1, 3, 5)])
    return np.abs(im - col).sum(2) <= tol


def hy(y):
    return round((y - cy) / r, 2)


def hx(x):
    return round((x - cx) / r, 2)


o = p.outfit
coat, skirt, belt, boots, hair, skin, tunic = (
    mask(o.coat_color),
    mask(o.skirt_color),
    mask(o.belt_color, 20),
    mask(o.boot_color),
    mask(p.hair_color),
    mask(p.skin_tone),
    mask(o.tunic_color),
)


def rows(m):
    ys = np.nonzero(m.any(1))[0]
    return (hy(ys.min()), hy(ys.max())) if len(ys) else None


def span(m, yhr, right_only=False):
    y = int(round(cy + yhr * r))
    xs = np.nonzero(m[y])[0]
    if right_only:
        xs = xs[xs > cx]
    return (hx(xs.min()), hx(xs.max())) if len(xs) else None


# the right half only for anything the held-out arm could touch
right = np.zeros(im.shape[:2], bool)
right[:, int(cx) :] = True
body_ink = (coat | tunic | belt | skirt) & ~mask("#ff00ff")
print("coat rows", rows(coat), "   ref top 1.13 hem 3.30")
print("belt rows", rows(belt), span(belt, (rows(belt)[0] + rows(belt)[1]) / 2), "   ref 2.30-2.54, x +-0.58")
print("skirt rows", rows(skirt), "   ref hem 4.26")
for yy, ref in ((1.26, "(0.36, 0.73)"), (1.6, "(0.18, 0.72)"), (2.07, "(0.22, 1.09) incl sleeve"), (3.1, "(0.36, 0.89)")):
    print(f"coat+tunic span right y={yy}", span(coat | tunic, yy, True), "  ref coatR", ref)
for yy, ref in ((3.45, "+-0.95/0.98"), (4.02, "+-1.11/1.16"), (4.14, "-0.84/0.97")):
    print(f"skirt span y={yy}", span(skirt, yy), "   ref", ref)
print("boots rows", rows(boots), span(boots, 5.1), span(boots, 5.8), "   ref 4.86-5.94, x -0.58..0.69 at 5.1, -0.79..0.74 at 5.8")
lab, n = ndi.label(skin & (np.arange(im.shape[0])[:, None] > cy + 4.0 * r))
for i in range(1, n + 1):
    ys, xs = np.nonzero(lab == i)
    if len(xs) > 200:
        print("leg", hx(xs.mean()), "half w", round((xs.max() - xs.min()) / 2 / r, 2), "rows", hy(ys.min()), hy(ys.max()))
print("   ref legs centres -0.33/+0.43, half w 0.23, visible 4.22-4.88")
hy_ = np.nonzero(hair.any(1))[0]
print("hair lowest", hy(hy_.max()), "   ref 2.60")
lab, n = ndi.label(skin & right & (np.arange(im.shape[0])[:, None] > cy + 2.0 * r) & (np.arange(im.shape[0])[:, None] < cy + 4.0 * r))
for i in range(1, n + 1):
    ys, xs = np.nonzero(lab == i)
    if len(xs) > 100:
        print("right hand centre", hx(xs.mean()), hy(ys.mean()), "   ref (1.20, 3.37)")
print("held hand centre", [round(v, 2) for v in c._hand_centre(sk, p, -1)], "   ref (-1.85, 2.64)")
