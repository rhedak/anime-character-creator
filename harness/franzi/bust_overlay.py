"""Overlay a proposed bust contour on the references, for the owner to correct. ./harness/run.sh harness/franzi/bust_overlay.py

Outlines only: no nipples, areolae or other detail. Solid where the contour is visible in the reference (the upper-inner edge,
seen as the shaded crescent in the V of ref 04), dashed where it is inferred (the outer side and the underside lie under cloth,
read from the cloth's own bulge and the underbust crease of the tight one-piece, ref 01). Points are in the 2x zoomed crop
coordinates of out/franzi/raw04.png (crop origin (440, 440) of the reference canvas). Writes out/franzi/bust-04.png and bust-01.png.
"""

import numpy as np
from PIL import Image, ImageDraw

OX, OY = 440, 440
CX_Z = (668.2 - OX) * 2  # the centre line in zoomed coordinates
# viewer's-left breast, from the cleavage bottom up the inside, over the top, down the outside and back along the underside
# Revised after the owner's note: the breasts' inner edges are the subtle shaded crescents either side of the centre line in
# the V of ref 04 (edge-filtered view: out/franzi/vedge-c.png). Read from that view, they start near the cup's upper edge, sweep
# inward and run almost vertical close to the centre line, meeting it near the bottom of the V.
# Second revision, from the owner's pink corrections on the first one (read from the owner's image: scale 1.243 against these
# coordinates, the right-hand polyline mirrored and averaged with the left): the inner edge is nearly straight up and down very
# close to the centre line, and the underside is not a curve round to the centre but follows the cup hem, a diagonal from the
# centre's low point out to the lowest point of the hem.
VISIBLE = [(370, 342), (405, 372), (435, 405), (447, 430), (450, 490), (452, 566)]
INFERRED = [(370, 342), (355, 336), (320, 330), (280, 335), (235, 358), (190, 400), (155, 455), (138, 520), (148, 590), (180, 635), (230, 664), (300, 674), (415, 625), (452, 566)]


def catmull(pts, n=14):
    p = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        for k in range(n):
            t = k / n
            q = [0.5 * ((2 * p[i][j]) + (-p[i - 1][j] + p[i + 1][j]) * t + (2 * p[i - 1][j] - 5 * p[i][j] + 4 * p[i + 1][j] - p[i + 2][j]) * t**2 + (-p[i - 1][j] + 3 * p[i][j] - 3 * p[i + 1][j] + p[i + 2][j]) * t**3) for j in (0, 1)]
            out.append(tuple(q))
    out.append(tuple(pts[-1]))
    return out


def mirror(pts):
    return [(2 * CX_Z - x, y) for x, y in pts]


def dashed(d, pts, color, on=7, off=5, width=3):
    run, state = 0.0, True
    for a, b in zip(pts, pts[1:]):
        seg = float(np.hypot(b[0] - a[0], b[1] - a[1]))
        if state:
            d.line([a, b], fill=color, width=width)
        run += seg
        if run >= (on if state else off):
            run, state = 0.0, not state


def main():
    for n, f, box in (("04", "ref/franzi/04-bikini-fullbody.png", (440, 440, 900, 860)), ("01", "ref/franzi/01-swimsuit.png", (440, 440, 900, 960))):
        im = Image.open(f).convert("RGBA")
        bg = Image.new("RGBA", im.size, "white")
        bg.alpha_composite(im)
        c = bg.convert("RGB").crop(box)
        c = c.resize((c.width * 2, c.height * 2))
        d = ImageDraw.Draw(c)
        for side in (lambda p: p, mirror):
            d.line(catmull(side(VISIBLE)), fill=(220, 0, 0), width=4)
            dashed(d, catmull(side(INFERRED)), (220, 0, 0))
        d.line([(CX_Z, 0), (CX_Z, c.height)], fill=(0, 120, 255), width=1)
        c.save(f"out/franzi/bust-{n}.png")
        if n == "04":
            # the same contour over the edge-filtered V, where the line can be seen
            lum = np.array(bg.convert("L")).astype(float)
            from scipy import ndimage

            hp = ndimage.gaussian_filter(lum, 2.0) - ndimage.gaussian_filter(lum, 8.0)
            ev = Image.fromarray(np.clip(128 + hp * 12, 0, 255).astype(np.uint8)).convert("RGB").crop(box)
            ev = ev.resize((ev.width * 2, ev.height * 2))
            d2 = ImageDraw.Draw(ev)
            for side in (lambda p: p, mirror):
                d2.line(catmull(side(VISIBLE)), fill=(255, 40, 40), width=3)
                dashed(d2, catmull(side(INFERRED)), (255, 40, 40), width=2)
            ev.save("out/franzi/bust-04-edges.png")
    print("wrote out/franzi/bust-04.png and bust-01.png")


if __name__ == "__main__":
    main()
