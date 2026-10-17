"""Fit circular arcs to the lid band and the aperture of each eye of ref 04, measured from the pixels.

    ./harness/run.sh harness/franzi/eye_arcs.py

The lid band is the connected black region over the eye. Its upper edge (black above, skin above that) and its lower edge (black
above, white or iris below) are traced column by column; a circle is fitted to each by least squares (Kasa). The aperture's outer
edge on the open side is the boundary of the white against the skin on the side away from the wing. Prints the fits and writes
out/franzi/eye-arcs.json (pixel coordinates of the reference canvas) and out/franzi/eye-arcs-{L,R}.png (the arcs drawn on the eye).
"""

import json

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

a = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")).astype(int)
rgb = a[..., :3]
lum = rgb.mean(2)
sat = rgb.max(2) - rgb.min(2)
dark = (lum < 70) & (a[..., 3] > 128)
white = (lum > 205) & (sat < 35)
skin = (np.abs(rgb - [0xFF, 0xD0, 0xB5]).sum(2) < 75)


def fit_circle(pts):
    x = np.array([p[0] for p in pts], float)
    y = np.array([p[1] for p in pts], float)
    A = np.stack([x, y, np.ones_like(x)], 1)
    b = -(x**2 + y**2)
    c = np.linalg.lstsq(A, b, rcond=None)[0]
    cx, cy = -c[0] / 2, -c[1] / 2
    r = float(np.sqrt(cx**2 + cy**2 - c[2]))
    rms = float(np.sqrt(np.mean((np.hypot(x - cx, y - cy) - r) ** 2)))
    return (float(cx), float(cy), r, rms)


out = {}
for name, box, seed in (("R", (690, 275, 790, 345), (725, 296)), ("L", (545, 280, 645, 350), (600, 300))):
    x0, y0, x1, y1 = box
    # the lid band: in each column the FIRST dark run below the brow gap (rows y0..y1), within the eye's own span; the hair beyond
    # the wing's tip and the iris ring below are other runs or other columns
    span = {"R": (698, 762), "L": (556, 622)}[name]
    upper, lower = [], []
    for x in range(span[0], span[1] + 1):
        col = dark[y0:y1, x]
        idx = np.nonzero(col)[0]
        if len(idx) == 0:
            continue
        start = idx[0]
        end = start
        while end + 1 < len(col) and col[end + 1]:
            end += 1
        upper.append((x, y0 + int(start)))
        lower.append((x, y0 + int(end)))
    # drop the wing's ends where the band becomes a thin point (keep columns where the band is at least 5 px thick)
    thick = [(x, u, l) for (x, u), (_, l) in zip(upper, lower) if l - u >= 5]
    up_pts = [(x, u) for x, u, _ in thick]
    lo_pts = [(x, l) for x, _, l in thick]
    fu, fl = fit_circle(up_pts), fit_circle(lo_pts)
    print(name, "lid upper edge circle cx,cy,r,rms", [round(v, 1) for v in fu], "x from", up_pts[0][0], "to", up_pts[-1][0])
    print(name, "lid lower edge circle cx,cy,r,rms", [round(v, 1) for v in fl])
    out[name] = {"upper": fu, "lower": fl, "x": [up_pts[0][0], up_pts[-1][0]], "up_pts": up_pts, "lo_pts": lo_pts}
    # draw
    Z = 8
    im = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    c = bg.convert("RGB").crop((x0 - 5, y0 - 20, x1 + 5, y1 + 25)).resize(((x1 - x0 + 10) * Z, (y1 - y0 + 45) * Z), Image.LANCZOS)
    d = ImageDraw.Draw(c)
    for (cx_, cy_, r_, _), col, pts in ((fu, (0, 200, 0), up_pts), (fl, (0, 200, 255), lo_pts)):
        xs = np.linspace(pts[0][0] - 3, pts[-1][0] + 3, 80)
        ys = cy_ + np.sqrt(np.maximum(r_**2 - (xs - cx_) ** 2, 0)) * (-1 if cy_ > np.mean([p[1] for p in pts]) else 1)
        d.line([((x - (x0 - 5)) * Z, (y - (y0 - 20)) * Z) for x, y in zip(xs, ys)], fill=col, width=3)
    for pts, col in ((up_pts, (255, 0, 0)), (lo_pts, (255, 0, 255))):
        for x, y in pts:
            px, py = (x - (x0 - 5)) * Z, (y - (y0 - 20)) * Z
            d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=col)
    c.save(f"out/franzi/eye-arcs-{name}.png")
json.dump(out, open("out/franzi/eye-arcs.json", "w"))
