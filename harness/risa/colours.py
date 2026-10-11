"""Risa's colours, modal-exact (`docs/risa-plan.md`, M10): for each layer the most common
exact RGB value in its eroded interior, in the composite, against what the preset has.

The first pass (M0) took a 6-level quantised histogram, good to a step per channel; this
takes the exact mode, the grade Satoko's palette was sampled to. Where a flat fill is
textured (her reference has a faint mottle) the mode is the fill, and the runner-up shows
how far the texture strays from it.

    ./harness/run.sh harness/risa/colours.py
"""

from collections import Counter

import numpy as np
from common import RGB, segment
from PIL import Image
from scipy import ndimage as ndi

from anime_character_creator.presets import RISA


def mode(mask, erode=4):
    inner = ndi.binary_erosion(mask, iterations=erode)
    px = RGB[inner if inner.sum() > 30 else mask]
    c = Counter(map(tuple, px.tolist()))
    (top, n), *rest = c.most_common(3)
    return top, n / len(px), [r[0] for r in rest]


def hexc(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def parse(h):
    return tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))


o = RISA.outfit
layers = {}
for name, seg, have in (
    ("hair", "long-black-hair.png", RISA.hair_color),
    ("blazer", "school-blazer.png", o.coat_color),
    ("skirt", "pleated-skirt.png", o.skirt_color),
    ("ribbon", "blue-ribbon.png", o.ribbon_color),
    ("shirt", "white-collared-shirt.png", o.tunic_color),
):
    m, _ = segment(seg)
    layers[name] = (m, have)
# Hair and blazer carry line work and a second tone: take the plain fill, the commonest
# value that is not the line's black, which `mode` does by being the commonest.
l1, _ = segment("brown-loafers/brown-loafers-1.png")
l2, _ = segment("brown-loafers/brown-loafers-2.png")
layers["loafers"] = (l1 | l2, o.boot_color)
for i in (1, 2, 3):
    # The gold buttons are crops at their own offsets: find them by colour in the blazer.
    pass

print(f"{'layer':<9}{'preset':<10}{'mode':<10}{'share':>7}  {'off by':>7}  runners-up")
for name, (m, have) in layers.items():
    top, share, rest = mode(m)
    d = np.abs(np.array(top) - np.array(parse(have))).max()
    print(f"{name:<9}{have:<10}{hexc(top):<10}{share:>6.0%}  {d:>7}  {[hexc(r) for r in rest]}")

# The socks and the skin are in the figure layer only: sample the socks where the legs are
# and the skin on the cheek.
fig = np.asarray(Image.open("ref-local/mio/segments/anime-girl.png").convert("RGBA")).astype(int)
OFF = (416, 47)


def box(x0, y0, x1, y1):
    sub = RGB[y0:y1, x0:x1].reshape(-1, 3)
    c = Counter(map(tuple, sub.tolist()))
    (top, n), *rest = c.most_common(3)
    return top, n / len(sub), [r[0] for r in rest]


for name, b, have in (
    ("sock", (545, 1180, 575, 1250), o.knee_sock_color),
    ("skin", (560, 330, 600, 360), RISA.skin_tone),
):
    top, share, rest = box(*b)
    d = np.abs(np.array(top) - np.array(parse(have))).max()
    print(f"{name:<9}{have:<10}{hexc(top):<10}{share:>6.0%}  {d:>7}  {[hexc(r) for r in rest]}")

print()
print("median of the eroded interior, per channel (the mottle's centre), and the mean:")
for name, (m, have) in layers.items():
    inner = ndi.binary_erosion(m, iterations=6)
    px = RGB[inner if inner.sum() > 30 else m]
    # Drop the line work's black and the second tones: keep the pixels near the median.
    med = np.median(px, axis=0)
    keep = px[np.abs(px - med).max(1) <= 8]
    print(
        f"{name:<9}{have:<10}median {hexc(np.median(px, axis=0).astype(int))}  "
        f"near-median mean {hexc(np.round(keep.mean(0)).astype(int))}  ({len(keep) / len(px):.0%} of pixels)"
    )
