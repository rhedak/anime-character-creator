"""Designed front locks (D5 todo step 4).

`shoulders.py` cut the traced front piece with a fixed-width band at the
shoulder row: the curtain ended in a flat stroked ledge, each lock ended in a
flat bottom edge with a sliver hooking on below it, and the lock's outer edge
followed raster pixels. Here the front piece keeps the curtain as traced down
to our shoulder row, and below it each side is drawn, not cut:

- **A funnel** from the curtain's cross-section at the shoulder row (from the
  neck side to the outermost hair) narrowing over `FUNNEL` head radii, both
  edges easing in (a smoothstep), into one lock `LOCK_W` wide. The hair that
  was wider than the lock goes behind the shoulder: the mass carries it, and
  the funnel's edge, not a cut across the curtain, is where the front stops.
- **The lock**: the width narrows to a point at `TIP` (our belt), on a centre
  line drifting `DRIFT` toward the body. The tip is the strand's own end.
- **Two strand lines** on each lock (uneven, converging on the tip), and the
  traced lines of the curtain cut at the funnel's end; every traced line whose
  middle lies below the shoulder is left to the mass.

The raster union of the curtain and the funnel and lock is traced and fitted
once, so there is one outline and no stroke along a cut. All measures are in
head radii, from `Skeleton` anchors (`shoulder_y`, `waist_y`) and the measured
inner edge of the reference's front hair; nothing is a pixel.

Reads `out/hair_only/hair.json` (the mass, the strands, the registration) and
writes `out/hair_only/hair_lock.json`, the same schema, so
`compare.py lock=out/hair_only/hair_lock.json` draws it. Also
`out/hair_only/locks.png`: the reference's front hair dimmed, the new front
piece green, what it drops red, the shoulder row yellow.
"""

import dataclasses
import json
import sys

sys.path.insert(0, "harness/hair_only")
sys.path.insert(0, "harness/trace_hair")

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import trace as T
import trace_lib as tl
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_only"
ORIGIN, S = T.ORIGIN, T.S
# Head radii.
FUNNEL = 0.75  # from the shoulder row to where the lock is one lock wide
LOCK_W = 0.38  # the original's front lock measures 0.36
DRIFT = 0.08  # how far the tip is toward the body from where the lock hangs
TIP_ABOVE_WAIST = 0.02  # the tip's height above our belt line
LOCK_IN_FALLBACK = 0.75  # the lock's neck-side edge if the reference's is lost
# The two lines on a lock: offset (fraction of the half width, outward), and
# how far down the lock (0 the funnel's end, 1 the tip) each runs.
LOCK_LINES = ((-0.42, 0.72), (0.38, 0.86))
STEP = 12  # px a tracked edge may move in one row
TOL_SHAPE, TOL_LINE = T.TOL_SHAPE, T.TOL_LINE


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def main() -> None:
    reg = json.load(open(f"{OUT}/register.json"))
    sc, (dx, dy) = reg["scale"], tuple(reg["offset"])
    hair = json.load(open(f"{OUT}/hair.json"))
    k = hair["squeeze"]
    px_r = S / sc  # raster px per head radius, across
    ox = (ORIGIN[0] - dx) / sc

    def h_to_y(hy):
        hu = T.CHEEK + (hy - T.CHEEK) / k if hy > T.CHEEK else hy
        return (ORIGIN[1] + hu * S - dy) / sc

    def y_to_h(y):
        hy = (y * sc + dy - ORIGIN[1]) / S
        return T.CHEEK + (hy - T.CHEEK) * k if hy > T.CHEEK else hy

    def to_head(pts):
        return [((x * sc + dx - ORIGIN[0]) / S, y_to_h(y)) for x, y in pts]

    img = np.asarray(Image.open(f"{T.DIR}/hair_only.png").convert("RGBA")).astype(float)
    front = T.alpha("hair_with_human_shape")
    full = T.alpha("hair_only") | front
    ow = T.outline_width(img, full)
    front_c = ndi.binary_erosion(front, iterations=max(1, int(round(ow / 2))))

    sk = c.skeleton_for(dataclasses.replace(PRESETS["katherina"], height=T.HEIGHT))

    def rel(v):
        return (v - sk.head_cy) / sk.head_r

    y_s, tip = rel(sk.shoulder_y), rel(sk.waist_y) - TIP_ABOVE_WAIST
    y1 = y_s + FUNNEL
    row_s = int(round(h_to_y(y_s)))
    print(f"shoulder {y_s:.3f} r (row {row_s}), funnel ends {y1:.3f}, tip {tip:.3f}")

    # The curtain as traced, down to the shoulder row (one blob).
    top = front_c.copy()
    top[row_s + 1 :] = False
    lab, _ = ndi.label(top)
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    top = lab == int(np.argmax(sizes))

    # Per side: the curtain's neck-side edge and outermost hair at the shoulder
    # row, and the neck-side edge of the reference's lock below the funnel.
    geo = {}
    for side in (-1, 1):
        xs = np.nonzero(top[row_s])[0]
        xs = xs[xs < ox] if side < 0 else xs[xs > ox]
        near, far = (xs.max(), xs.min()) if side < 0 else (xs.min(), xs.max())
        inner = {}
        edge = float(near)
        for y in range(row_s, front_c.shape[0]):
            row = np.nonzero(front_c[y])[0]
            row = row[np.abs(row - edge) <= STEP]
            row = row[row < ox] if side < 0 else row[row > ox]
            if not len(row):
                break
            edge = float(row.max() if side < 0 else row.min())
            inner[y] = abs(edge - ox) / px_r
        ys = [y for y in inner if y1 - 0.1 <= y_to_h(y) <= y1 + 0.5]
        lock_in = float(np.median([inner[y] for y in ys])) if ys else LOCK_IN_FALLBACK
        geo[side] = dict(in_top=abs(near - ox) / px_r, out_top=abs(far - ox) / px_r, lock_in=lock_in)
        print(f"side {side:+d}: curtain {geo[side]['in_top']:.2f}..{geo[side]['out_top']:.2f} r, lock neck edge {lock_in:.2f} r")

    def edges(g, hy):
        """The front piece's neck-side and outer edge below the shoulder, as
        distances from the body's centre line, in head radii."""
        if hy <= y1:
            e = smooth((hy - y_s) / FUNNEL)
            return g["in_top"] + (g["lock_in"] - g["in_top"]) * e, g["out_top"] + (g["lock_in"] + LOCK_W - g["out_top"]) * e
        u = (hy - y1) / (tip - y1)
        half = LOCK_W / 2 * (1 - u**1.8) ** 0.9
        mid = g["lock_in"] + LOCK_W / 2 - DRIFT * u * u
        return mid - half, mid + half

    new = top.copy()
    for y in range(row_s + 1, int(h_to_y(tip)) + 1):
        hy = y_to_h(y)
        if hy >= tip:
            break
        for side, g in geo.items():
            a, b = edges(g, hy)
            lo, hi = sorted((ox + side * a * px_r, ox + side * b * px_r))
            new[y, int(round(lo)) : int(round(hi)) + 1] = True
    lab, _ = ndi.label(new)
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    new = lab == int(np.argmax(sizes))

    def parts(mm, min_px=200):
        res = []
        lab_p, n_p = ndi.label(mm)
        for i in range(1, n_p + 1):
            piece = lab_p == i
            if piece.sum() < min_px:
                continue
            outer = tl.fit_closed(to_head(tl.boundary(piece)), TOL_SHAPE)
            holes = []
            hl, nh = ndi.label(ndi.binary_fill_holes(piece) & ~piece)
            for j in range(1, nh + 1):
                if (hl == j).sum() >= min_px:
                    holes.append(tl.fit_closed(to_head(tl.boundary(hl == j)), TOL_SHAPE))
            res.append([outer, holes])
        return res

    front_parts = parts(new)
    largest = max(front_parts, key=lambda pr: len(pr[0][1]))[0]
    print(f"front: {len(front_parts)} pieces, {sum(len(h) for _, h in front_parts)} holes")

    def raster_of(hx, hy):
        return int(round((hx * S + ORIGIN[0] - dx) / sc)), int(round(h_to_y(hy)))

    def in_new(pt):
        x, y = raster_of(*pt)
        return 0 <= y < new.shape[0] and 0 <= x < new.shape[1] and bool(new[y, x])

    # The traced lines: a line on the front piece is cut where the funnel ends.
    strands, n_cut, n_back = [], 0, 0
    for st in hair["strands"]:
        pts = tl.sample_chain(*st["chain"])
        if not in_new(pts[len(pts) // 2]):
            strands.append({**st, "front": False})
            n_back += 1
            continue
        kept = [p for p in pts if p[1] <= y1]
        if len(kept) < 8:
            strands.append({**st, "front": False})
            n_back += 1
            continue
        n_cut += len(kept) < len(pts)
        strands.append({**st, "front": True, "chain": tl.fit_chain(kept, tl.simplify(kept, TOL_LINE))})
    print(f"traced lines: {sum(s['front'] for s in strands)} on the front piece ({n_cut} cut at the funnel), {n_back} on the mass")

    # The lock's own lines.
    lines = []
    for side, g in geo.items():
        for off, reach in LOCK_LINES:
            hy_end = y1 + reach * (tip - y1)
            pts = []
            for hy in np.linspace(y1 - 0.2, hy_end, 24):
                a, b = edges(g, float(hy))
                mid, half = (a + b) / 2, (b - a) / 2
                pts.append((side * (mid + off * half), float(hy)))
            lines.append({"chain": tl.fit_chain(pts, tl.simplify(pts, TOL_LINE)), "front": True, "px": 0})
    strands.extend(lines)

    out = {**hair, "front_parts": front_parts, "front": largest, "front_edges": [largest], "strands": strands}
    out["locks"] = dict(funnel=FUNNEL, lock_w=LOCK_W, drift=DRIFT, tip=tip, shoulder=y_s)
    json.dump(out, open(f"{OUT}/hair_lock.json", "w"), indent=1)

    view = np.where(front[..., None], np.clip(img[..., :3] * 2.2, 0, 255), 255)
    view[front_c & ~new] = (220, 60, 60)
    view[new] = (60, 180, 70)
    im = Image.fromarray(view.astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.line([(0, row_s), (im.width, row_s)], fill=(255, 220, 0), width=3)
    for ln in lines:
        d.line([raster_of(*q) for q in tl.sample_chain(*ln["chain"])], fill=(0, 60, 200), width=3)
    im.crop((200, 250, 1120, 1450)).resize((690, 900)).save(f"{OUT}/locks.png")
    print(f"{OUT}/hair_lock.json, {OUT}/locks.png")


if __name__ == "__main__":
    main()
