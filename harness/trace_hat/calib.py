"""Measure face/hair landmarks on our render (no hat) and on the reference.

Our side is reported directly in head radii via the skeleton, so the
reference's landmarks can be matched to known head-radius positions.
"""

import dataclasses
import io

import cairosvg
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from anime_character_creator.character import render_character
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import build_skeleton

REF = "/Users/henrik/git/time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OUT = "out/trace_hat"

p = PRESETS["katherina"]
p = dataclasses.replace(p, outfit=dataclasses.replace(p.outfit, hat_color=None))
sk = build_skeleton(heads=p.heads, frame=p.frame)
K = 3
svg = render_character(p, sk, background="black")
png = cairosvg.svg2png(bytestring=svg.encode(), scale=K)
im = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(int)
Image.fromarray(im.astype("uint8")).save(f"{OUT}/ours_nohat.png")
cx, cy, r = sk.head_cx * K, sk.head_cy * K, sk.head_r * K
print("ours canvas", im.shape, "head", cx, cy, r, "skin", p.skin if hasattr(p, "skin") else "")


def hr_y(py):
    return (py - cy) / r


def hr_x(px):
    return (px - cx) / r


def skin_mask(a, ref_col):
    d = np.abs(a - np.array(ref_col)).sum(2)
    return d < 60


def report(name, a, skin_col, hair_col, to_x, to_y):
    sm = skin_mask(a, skin_col)
    lab, _ = ndi.label(sm)
    # largest skin component in the upper half = the face
    sizes = ndi.sum(sm, lab, range(1, lab.max() + 1))
    face = lab == (int(np.argmax(sizes)) + 1)
    ys, xs = np.nonzero(face)
    print(name, "face bbox y", to_y(ys.min()), to_y(ys.max()), "x", to_x(xs.min()), to_x(xs.max()))
    for fy in np.linspace(ys.min(), ys.max(), 9).astype(int):
        row = np.nonzero(face[fy])[0]
        print("   face row", round(to_y(fy), 3), "x", round(to_x(row.min()), 3), round(to_x(row.max()), 3))
    hm = np.abs(a - np.array(hair_col)).sum(2) < 70
    lab, _ = ndi.label(hm)
    sizes = ndi.sum(hm, lab, range(1, lab.max() + 1))
    hair = lab == (int(np.argmax(sizes)) + 1)
    ys, xs = np.nonzero(hair)
    print(name, "hair bbox y", round(to_y(ys.min()), 3), "x", round(to_x(xs.min()), 3), round(to_x(xs.max()), 3))
    for fy in np.linspace(ys.min(), ys.min() + (ys.max() - ys.min()) * 0.5, 8).astype(int):
        row = np.nonzero(hair[fy])[0]
        print("   hair row", round(to_y(fy), 3), "x", round(to_x(row.min()), 3), round(to_x(row.max()), 3))


# sample our own face/hair colours from the render
print("ours face px", im[int(cy + 0.5 * r), int(cx)], "hair px", im[int(cy - 1.05 * r), int(cx)])
report("OURS", im, im[int(cy + 0.5 * r), int(cx)], im[int(cy - 1.05 * r), int(cx)], hr_x, hr_y)

ref = np.asarray(Image.open(REF).convert("RGB")).astype(int)
print("REF (raw px)")
report("REF", ref, ref[560, 650], ref[340, 560], lambda x: x, lambda y: y)
