"""D5 plan, step 3, part 2: the regions (`regions.py`) walked, cut at their named
points and fitted, in head radii (`docs/detail-status.md`, D5 plan).

The chains, each in the order the renderer wants it:

- `mass`: the silhouette as an open edge, from the left outer fall's inner
  tip up the left side, over the crown, down the right side to the right
  outer fall's inner tip. The renderer closes it behind the body, as
  `long_traced` does. Marks forced at the crown's apex and at both seams'
  outer ends (`Q`), so the front piece can retrace the mass's own segments
  between them.
- `line`: the hairline, from the left front lock's lowest tip up its inner
  edge, round the face opening, down to the right front lock's lowest tip.
- `lock_l`, `lock_r`: each front lock's outer edge, from the seam's inner end
  (`T`) down to the lowest tip, a mark forced at the top of the dark strip
  (the apex, where the outer fall's edge leaves it).
- `under_l`, `under_r`: each outer fall's inner edge, from the apex down to
  the fall's inner tip: the line between the outer fall and the darker hair
  behind.

Each chain is simplified (Douglas-Peucker) at `TOL` and then has marks taken
out, shortest first, until no segment is shorter than two stroke widths
(0.0854 head radii, `_stroke_w` being 0.0427 at every height): the rule the
crop's 26 segments and `long_traced`'s 28 were chosen by. Forced marks stay.

Writes `out/hair_parted/trace.json` and `overlay.png` (every chain over the
reference, brightened, and a 3x crop of each side).

    ./harness/run.sh harness/hair_parted/trace.py
"""

import json
import sys

sys.path.insert(0, "harness/hair_parted")
sys.path.insert(0, ".claude/skills/trace-reference")

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import regions as R
import trace_lib as tl

OUT = "out/hair_parted"
TOL = 0.012
MIN_SEG = 2 * 0.0427
APEX_W = 0.08
COLOURS = {
    "mass": (255, 255, 255),
    "line": (255, 60, 60),
    "lock_l": (255, 200, 0),
    "lock_r": (255, 200, 0),
    "under_l": (0, 230, 255),
    "under_r": (0, 230, 255),
}


def contour(mask):
    """The mask's outer boundary, clockwise on screen, as an (N, 2) array of
    pixel (x, y)."""
    return np.array(tl.boundary(mask), dtype=float)


def nearest(pts, q):
    return int(np.argmin(((pts - np.asarray(q)) ** 2).sum(1)))


def walk(pts, i, j):
    """Points from index `i` to `j` along a closed contour, forward."""
    n = len(pts)
    if j >= i:
        return pts[i : j + 1]
    return np.concatenate([pts[i:], pts[: j + 1]])


def to_r(pts, cal):
    ox, oy, s = cal
    return [((x - ox) / s, (y - oy) / s) for x, y in pts]


def fit(points, forced=(), tol=TOL):
    """Simplify, drop marks under `MIN_SEG` shortest first (never a forced one
    or an end), fit. `forced` are indices into `points`. Returns the chain and
    the positions of the forced marks in its segment list (the index of the
    segment that ends on each)."""
    xy = np.asarray(points)
    marks = sorted(set(tl.simplify(list(map(tuple, xy)), tol)) | set(forced) | {0, len(xy) - 1})
    keep = set(forced) | {0, len(xy) - 1}
    while True:
        seg = [np.hypot(*(xy[b] - xy[a])) for a, b in zip(marks, marks[1:])]
        short = [k for k, ln in enumerate(seg) if ln < MIN_SEG]
        if not short:
            break
        # The shortest segment loses whichever of its ends is not forced.
        k = min(short, key=lambda k: seg[k])
        a, b = marks[k], marks[k + 1]
        drop = b if b not in keep else a if a not in keep else None
        if drop is None:
            break
        marks.remove(drop)
    chain = tl.fit_chain(list(map(tuple, xy)), marks)
    at = {f: marks.index(f) - 1 for f in forced}
    return chain, at


def main() -> None:
    z = np.load(f"{OUT}/regions.npz")
    mass, front, outer = z["mass"], z["front"], z["outer"]
    cal = tuple(z["cal"])
    ox, oy, s = cal
    (tlx, tly), (trx, try_) = z["t"]
    behind = mass & ~front & ~outer

    # Mass: the closed contour, opened at the chord across the bottom (the run
    # along the lowest filled row between the two falls).
    mc = contour(mass)
    rows = np.nonzero(mass.any(1))[0]
    c0 = int(round(ox))
    # The chord: the lowest row whose filled run crosses the centre line.
    chord_y = max(y for y in rows if mass[y, c0])
    # The chord's ends: the filled run along that row through the centre line.
    row = mass[chord_y]
    xa = c0 - int(np.argmax(~row[c0::-1]))
    xb = c0 + int(np.argmax(~row[c0:])) - 1
    left_end = nearest(mc, (xa, chord_y))
    right_end = nearest(mc, (xb, chord_y))
    # Of the two ways round from the left end to the right end, the chord is
    # the short one; the edge is the long way, up the left side.
    a = walk(mc, left_end, right_end)
    b = walk(mc[::-1], len(mc) - 1 - left_end, len(mc) - 1 - right_end)
    open_pts = a if len(a) > len(b) else b
    # Seams' outer ends: where each seam's row meets the silhouette.
    ql = (np.nonzero(mass[int(tly)])[0].min(), tly)
    qr = (np.nonzero(mass[int(try_)])[0].max(), try_)
    i_ql, i_qr = nearest(open_pts, ql), nearest(open_pts, qr)
    i_crown = int(np.argmin(open_pts[:, 1]))
    mass_r = to_r(open_pts, cal)
    mass_chain, mass_at = fit(mass_r, forced=(i_ql, i_crown, i_qr))

    # Front: the closed contour, cut at each lock's lowest tip and each T.
    fc = contour(front)
    fr = np.asarray(to_r(fc, cal))
    low = fr[:, 1] > 1.2
    tip_l = int(np.argmax(np.where(low & (fr[:, 0] < 0), fr[:, 1], -9)))
    tip_r = int(np.argmax(np.where(low & (fr[:, 0] > 0), fr[:, 1], -9)))
    i_tl = nearest(fc, (tlx, tly))
    i_tr = nearest(fc, (trx, try_))
    # The hairline: from the left tip to the right tip the way that passes the
    # face (the inner side), i.e. not through the T points.
    fwd = walk(fc, tip_l, tip_r)
    if any(np.allclose(fc[i_tl], q) for q in fwd):
        line_px = walk(fc[::-1], len(fc) - 1 - tip_l, len(fc) - 1 - tip_r)
        rev = True
    else:
        line_px = fwd
        rev = False
    line_chain, _ = fit(to_r(line_px, cal))

    # The reference's darker tone, the hair behind: its large pieces only
    # (the wedges by the neck and the two strips), not antialiased line edges.
    _, A, lum, _ = R.load()
    dark = A & (lum >= R.LINE) & (lum < R.DARK)
    lab, n = ndi.label(dark)
    sizes = ndi.sum(dark, lab, range(1, n + 1))
    strip = np.isin(lab, 1 + np.nonzero(sizes >= 400)[0])

    # Each lock's outer edge, from T down to its tip, the apex forced: where
    # the dark strip outside it first reaches `APEX_W` across. It starts as a
    # sliver about 0.04 head radii wide near 0.9; drawn from there, the outer
    # fall's edge and the lock's would run under a stroke apart and read as one
    # heavy line. Searched below the ear, whose hole in the reference sits
    # beside the edge at 0.14 to 0.43 head radii.
    def lock(i_t, i_tip, side):
        a = walk(fc, i_t, i_tip)
        b = walk(fc[::-1], len(fc) - 1 - i_t, len(fc) - 1 - i_tip)
        # The lock's edge is the short way from T to the tip.
        a = a if len(a) < len(b) else b
        apex = None
        for k, (x, y) in enumerate(a):
            if (y - oy) / s < 0.9:
                continue
            # The run of hair that is not light, outward from just past the
            # lock's line.
            yo, xo, w = int(round(y)), int(round(x + side * 2)), 0
            while A[yo, xo] and lum[yo, xo] < R.DARK and w < 60:
                xo += side
                w += 1
            if w >= APEX_W * s and strip[yo, int(round(x + side * (2 + w / 2)))]:
                apex = k
                break
        assert apex is not None, "no dark strip beside the lock"
        chain, at = fit(to_r(a, cal), forced=(apex,))
        return chain, at[apex], a[apex]

    lock_l, apex_at_l, apex_l = lock(i_tl, tip_l, -1)
    lock_r, apex_at_r, apex_r = lock(i_tr, tip_r, 1)

    # The outer falls' inner edges: from the apex down, along the outer
    # region's contour, while the hair just inside it is behind.
    def under(side, apex):
        half = np.zeros_like(outer)
        if side < 0:
            half[:, :c0] = True
        else:
            half[:, c0:] = True
        lab, n = ndi.label(outer & half)
        sizes = ndi.sum(outer & half, lab, range(1, n + 1))
        blob = lab == 1 + int(np.argmax(sizes))
        oc = contour(blob)
        n = len(oc)
        k0 = nearest(oc, apex)
        # Which way round runs down the inner side: the inner side is the one
        # nearer the centre line.
        step = 1 if abs(oc[(k0 + 8) % n, 0] - ox) < abs(oc[(k0 - 8) % n, 0] - ox) else -1
        if oc[(k0 + 8 * step) % n, 1] < oc[k0, 1]:
            step = -step
        run, k, misses = [], k0, 0
        while misses < 6 and len(run) < n:
            x, y = oc[k % n]
            xi, yi = int(round(x - side * 3)), int(round(y))
            if behind[yi, xi] or strip[yi, xi]:
                misses = 0
            else:
                misses += 1
            run.append((x, y))
            k += step
        run = np.array(run[: len(run) - misses])
        chain, _ = fit(to_r(run, cal))
        return chain

    under_l = under(-1, apex_l)
    under_r = under(1, apex_r)

    lowest = max(y for _, y in mass_r)
    out = {
        "calibration": {"origin": [ox, oy], "px_per_r": s},
        "base_tip": lowest,
        "mass": mass_chain,
        "mass_seam_l": mass_at[i_ql],
        "mass_crown": mass_at[i_crown],
        "mass_seam_r": mass_at[i_qr],
        "line": line_chain,
        "lock_l": lock_l,
        "lock_r": lock_r,
        "lock_apex_l": apex_at_l,
        "lock_apex_r": apex_at_r,
        "under_l": under_l,
        "under_r": under_r,
    }
    json.dump(out, open(f"{OUT}/trace.json", "w"), indent=1)
    for k in ("mass", "line", "lock_l", "lock_r", "under_l", "under_r"):
        (st, segs) = out[k]
        lens = []
        p = st
        for _, e in segs:
            lens.append(np.hypot(e[0] - p[0], e[1] - p[1]))
            p = e
        print(f"{k:8}: {len(segs):3} segments, shortest {min(lens):.3f} r; start ({st[0]:+.3f}, {st[1]:+.3f}) end ({p[0]:+.3f}, {p[1]:+.3f})")
    print(
        f"mass: seams at segments {out['mass_seam_l']} and {out['mass_seam_r']}, crown {out['mass_crown']}; "
        f"lowest point {lowest:.3f} r; lock apexes at {apex_at_l}, {apex_at_r}"
    )

    # Overlay.
    comp = np.asarray(Image.open(f"{R.REF}/katherina_grok_nohat.png").convert("RGB")).astype(float)
    im = Image.fromarray(np.clip(comp * 2.4, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for k, col in COLOURS.items():
        pts = tl.sample_chain(*out[k], per_segment=16)
        d.line([(ox + x * s, oy + y * s) for x, y in pts], fill=col, width=2)
        st = out[k][0]
        marks = [st] + [e for _, e in out[k][1]]
        for x, y in marks:
            px, py = ox + x * s, oy + y * s
            d.ellipse([px - 2.5, py - 2.5, px + 2.5, py + 2.5], outline=col)
    im.crop((330, 180, 1000, 1000)).save(f"{OUT}/overlay.png")
    for name, box in (("left", (355, 420, 620, 990)), ("right", (690, 420, 975, 990))):
        c = im.crop(box)
        c.resize((c.width * 2, c.height * 2), Image.LANCZOS).save(f"{OUT}/overlay_{name}.png")
    print(f"{OUT}/overlay.png, overlay_left.png, overlay_right.png")


if __name__ == "__main__":
    main()
