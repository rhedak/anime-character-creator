"""The reference's hair with what hides it filled in (the owner, 2026-09-29:
the segment has only what shows, so the rest is interpolated or
extrapolated). Replaces `trace_hair.py`'s stand-ins (a circle for the crown,
the left mirrored under the bat, each side's convex hull behind the body),
which our figure shows, since its arms are thinner and its hat smaller than
the reference's.

Everything is in the composite's pixels. The occluders are `segments/`'s exact
cuts (`occlusion.py`): hat, bat, dress (the jacket and the arms), collar,
belt, staff.

**Hair falls, so it is filled along its fall.**

- **The outer edges, row by row.** On each row, each side's outermost hair
  pixel is a *seen* edge where the page beyond it is open for `CLEAR` px, a
  *hidden* one where an occluder comes sooner. A run of hidden rows with seen rows on both sides
  is a cubic Hermite between them, matching the seen edge's position and
  slope at both ends (the slope a line fitted over `SLOPE_ROWS` seen rows).
  Below the lowest seen row the edge carries straight on; the bottom edge
  decides where the hair ends.
- **The bottom edge, column by column,** the same way: the lowest hair pixel
  of the back hair is seen where page lies under it, hidden where an occluder
  does. Hidden columns take a monotone cubic through the seen ones
  (`PchipInterpolator`), held level beyond the outermost.
- **The crown, extrapolated:** nothing shows above the brim, so each side's
  outer edge goes on from its highest seen row with its own slope, as a cubic
  Bezier into a top point over the parting at `CROWN_TOP` head radii, level
  there. The top is a decision, not a measurement: 0.25 head radii over the
  skull, as `long_traced`'s crown, inside the canvas's hair ceiling (-1.36).
- **The front locks** lie over the jacket, so for the back hair they count as
  occluders, and their own tips as seen.

The back hair is the region between the two outer edges, from the crown down
to the bottom edge, joined with what shows, but never over page that shows
(a first version filled the gaps between the sheets and the arms, and the
hair read as a block). The front piece is what shows
above `SPLIT`, the front locks below it, and the back hair only where the hat
or the bat hid it: filled from the jacket and the collar too, it would lay
the back hair over the body.

Writes `out/trace_hair/filled.npz` (the two masks) and `filled.png`: what
shows in purple, what was filled in orange (back) and green (front), the seen
edge rows as white dots, the hidden ones red.
"""

import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, "harness/trace_hair")
from occlusion import masks

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
OUT = "out/trace_hair"
ORIGIN, S = (636, 290), 88.7
GROW = 2
SPLIT = 2.05
FRONT_X = 1.3
SLOPE_ROWS = 12
CROWN_TOP = -1.25
OCCLUDE_PAD = 3
# An edge is seen only with open page for this many pixels beyond it (0.25
# head radii): the gaps between the bat's wings and body are page, and read
# as seen hair edges without it.
CLEAR = 22


def page_mask(a, cuts):
    """The page: near-black outside every cut and connected to the picture's
    border. Dark alone takes the pupils, lashes and the face's own lines as
    page too."""
    dark = (a.astype(int).sum(2) < 40) & ~ndi.binary_dilation(cuts, iterations=GROW + 1)
    lab, _ = ndi.label(dark)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    return np.isin(lab, border[border > 0])


def edges(V, O, side):
    """Per row, the outermost hair pixel on one side of the centre line and
    whether it is seen (page beyond it) or hidden (an occluder beyond it)."""
    H, W = V.shape
    ox = ORIGIN[0]
    xs = np.full(H, np.nan)
    seen = np.zeros(H, bool)
    for y in range(H):
        row = np.nonzero(V[y, :ox] if side < 0 else V[y, ox:])[0]
        if not len(row):
            continue
        x = row.min() if side < 0 else ox + row.max()
        span = O[y, max(0, x - CLEAR) : x] if side < 0 else O[y, x + 1 : x + 1 + CLEAR]
        xs[y] = x
        seen[y] = len(span) == CLEAR and not span.any()
    return xs, seen


def slope_at(ys, xs, n):
    if len(ys) < 2:
        return 0.0
    ys, xs = ys[:n], xs[:n]
    return float(np.polyfit(ys, xs, 1)[0]) if len(ys) >= 2 else 0.0


def fill_edge(xs, seen):
    """Hidden rows between seen ones as cubic Hermites; below the lowest seen
    row carried straight on. Returns the filled edge and the rows it covers
    (from the highest seen row down)."""
    out = xs.copy()
    rows = np.nonzero(seen)[0]
    top, bottom = rows.min(), rows.max()
    for y in range(top, bottom + 1):
        if seen[y]:
            continue
        a = rows[rows < y].max()
        b = rows[rows > y].min()
        if y != a + 1:
            continue
        above = rows[(rows <= a) & (rows > a - 3 * SLOPE_ROWS)][::-1]
        below = rows[(rows >= b) & (rows < b + 3 * SLOPE_ROWS)]
        ma = slope_at(above, xs[above], SLOPE_ROWS)
        mb = slope_at(below, xs[below], SLOPE_ROWS)
        h = b - a
        for yy in range(a + 1, b):
            t = (yy - a) / h
            h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
            out[yy] = h00 * xs[a] + h10 * h * ma + h01 * xs[b] + h11 * h * mb
    out[bottom + 1 :] = out[bottom]
    return out, top


def mirrored_fill(fl, top_l, er, sr):
    """The right edge where it hides: the left's filled edge mirrored about
    the centre line, plus the right's own departure from it, which is
    measured on its seen rows and interpolated linearly between them (held
    beyond the outermost). The brim hides the right edge down to the cheek
    and the bat from there to the shoulder, about two head radii with no seen
    row: a Hermite across that has nothing to go on, and the left side, seen
    nearly all the way down, is the best guide to its shape."""
    ox = ORIGIN[0]
    prior = 2 * ox - fl
    rows = np.nonzero(sr & ~np.isnan(prior))[0]
    dev = er[rows] - prior[rows]
    allr = np.arange(len(fl))
    d = np.interp(allr, rows, dev)
    out = prior + d
    out[:top_l] = np.nan
    return out, top_l


def crown(edge_l, top_l, edge_r, top_r, apex, H, W):
    """The crown's outline as a polygon: each side's edge from its highest
    seen row on, with its slope, a cubic Bezier into `apex`, level there."""
    def side(edge, top, sgn):
        rows = np.arange(top, top + SLOPE_ROWS * 2)
        m = slope_at(rows, edge[rows], SLOPE_ROWS * 2)
        p0 = np.array([edge[top], top], float)
        up = np.array([-m, -1.0]) / np.hypot(m, 1)
        reach = np.hypot(apex[0] - p0[0], apex[1] - p0[1])
        p1 = p0 + up * reach * 0.45
        p2 = np.array(apex, float) + np.array([sgn * reach * 0.45, 0.0])
        t = np.linspace(0, 1, 60)[:, None]
        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * np.array(apex, float)

    left = side(edge_l, top_l, -1)
    right = side(edge_r, top_r, 1)
    return [*map(tuple, left), *map(tuple, right[::-1])]


def main() -> None:
    a = np.asarray(Image.open(REF).convert("RGB"))
    H, W = a.shape[:2]
    ms = masks((H, W))
    ox, oy = ORIGIN
    hair = ms["purple-hair"]
    occ = np.zeros((H, W), bool)
    for n in ("witch-hat", "black-bat", "dark-blue-dress", "yellow-collar", "brown-belt", "wooden-staff"):
        occ |= ms[n]
    occ_d = ndi.binary_dilation(occ, iterations=OCCLUDE_PAD)
    V = ndi.binary_dilation(hair, iterations=GROW) & ~occ | hair
    Y, X = np.mgrid[0:H, 0:W]
    split = int(oy + SPLIT * S)

    # The front locks: what shows below the split, touching it, inside FRONT_X.
    below = V & (Y >= split)
    lab, n = ndi.label(below)
    locks = np.zeros_like(V)
    for i in range(1, n + 1):
        k = lab == i
        ys, xs_ = np.nonzero(k)
        if k.sum() > 150 and ys.min() <= split + 1 and abs((xs_.mean() - ox) / S) < FRONT_X:
            locks |= k
    Vb = V & ~locks
    Ob = occ_d | ndi.binary_dilation(locks, iterations=OCCLUDE_PAD)

    el, sl = edges(Vb, Ob, -1)
    er, sr = edges(Vb, Ob, 1)
    fl, top_l = fill_edge(el, sl)
    fr, top_r = mirrored_fill(fl, top_l, er, sr)

    # The parting: the face opening's top between the two sides, on the brim row.
    brim = int(np.nonzero(V.any(1))[0].min())
    gap = np.nonzero(~V[brim + 2, ox - 60 : ox + 60])[0]
    part_x = ox - 60 + (gap.mean() if len(gap) else 60)
    apex = (part_x, oy + CROWN_TOP * S)
    print(f"brim row {(brim - oy) / S:+.3f}, parting x {(part_x - ox) / S:+.3f}, highest seen edge rows {(top_l - oy) / S:+.3f} / {(top_r - oy) / S:+.3f}")
    poly = crown(fl, top_l, fr, top_r, apex, H, W)
    im = Image.new("1", (W, H), 0)
    ImageDraw.Draw(im).polygon(poly, fill=1)
    crown_m = np.asarray(im, bool)

    # The bottom edge of the back hair, per column.
    lo, hi = int(np.nanmin(fl)), int(np.nanmax(fr))
    cols = np.arange(lo, hi + 1)
    yb = np.full(len(cols), np.nan)
    seen_b = np.zeros(len(cols), bool)
    for i, x in enumerate(cols):
        ys = np.nonzero(Vb[:, x])[0]
        if not len(ys):
            continue
        y = ys.max()
        yb[i] = y
        seen_b[i] = y + 1 < H and not Ob[y + 1, x] and y > oy + SPLIT * S
    xs_seen, ys_seen = cols[seen_b], yb[seen_b]
    f = PchipInterpolator(xs_seen, ys_seen, extrapolate=False)
    ybf = f(cols)
    ybf = np.where(cols < xs_seen.min(), ys_seen[0], ybf)
    ybf = np.where(cols > xs_seen.max(), ys_seen[-1], ybf)
    print(f"bottom edge: {seen_b.sum()} seen columns of {len(cols)}")

    back = np.zeros((H, W), bool)
    for y in range(min(top_l, top_r), H):
        if np.isnan(fl[y]) or np.isnan(fr[y]):
            continue
        back[y, int(fl[y]) : int(fr[y]) + 1] = True
    col_ok = np.zeros((H, W), bool)
    for i, x in enumerate(cols):
        col_ok[: int(ybf[i]) + 1, x] = True
    back &= col_ok
    back |= crown_m
    # Never over page that shows: the gaps between a back sheet and the arm,
    # between the tips, under the outer sheets were seen empty, and filling
    # them read as a block (`audit.py`: 8 of the segment's 15 tips lost). Page
    # is the near-black ground outside every cut; anything else that is not
    # hair (the face, the neck, the occluders) hid what is behind it.
    page = page_mask(a, occ | hair)
    back &= ~page
    back |= Vb

    hidden_by = ms["witch-hat"] | ms["black-bat"]
    hid = ndi.binary_dilation(hidden_by, iterations=OCCLUDE_PAD)
    # Only where the hat or the bat hid it: the crown's outline starts at the
    # outer edges' highest seen rows, at the cheek (the brim is wide), so its
    # chord crosses the face, which is seen and is not hair.
    front = (V | ((back | crown_m) & hid)) & (Y < split) | locks
    np.savez_compressed(f"{OUT}/filled.npz", back=back, front=front)

    v = a.astype(float) * 0.45
    v[back & ~V] = (240, 150, 40)
    v[front & ~V] = (60, 200, 80)
    v[V] = 0.4 * v[V] + 0.6 * np.array((150, 70, 200))
    for y in range(H):
        for xs, sn in ((el, sl), (er, sr)):
            if not np.isnan(xs[y]):
                v[y, int(xs[y])] = (255, 255, 255) if sn[y] else (255, 0, 0)
    x0, y0, x1, y1 = (400, 150, 880, 1000)
    Image.fromarray(v[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.NEAREST).save(
        f"{OUT}/filled.png"
    )
    print(f"{OUT}/filled.png")


if __name__ == "__main__":
    main()
