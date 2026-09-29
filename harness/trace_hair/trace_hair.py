"""Trace `ref-local/katherina_grok_real/`'s hair and fill in what it hides
(the trace skill, steps 3 and 4), in our head radii and on our body.

The owner's call (2026-09-29), after D5's study: drawn-in strand lines made
our hair worse, and the only thing that reads is the reference's own hair,
traced, its gaps filled in. The reference is otherwise never traced (the
detail plan's decision 4); this is the second exception, after the hands.

**The masks** are the composite's own pixels: `segments/`'s hair, hat and bat
are exact cuts of it (`locate.py`). What hides the hair is filled in, all in
the reference's pixels, before anything is measured:

- the crown under the hat: a circle fitted to the hair's outer edge between
  the brim and the cheek, inside the hat's own mask;
- the right side under the bat: the left side mirrored about the head's
  centre line, inside the bat's mask only, so the right keeps its own shape
  wherever it shows;
- behind the body (the mass only): each side's back hair below the split
  line, closed into one piece by its convex hull, the arm and the torso
  covering the hull's straight edges.

**Front and back.** Above `SPLIT` (the row where the reference's left arm
comes out between its front lock and its back sheet) all the hair is front;
below it, the front locks (the pieces touching the split row inside
`FRONT_X`), and everything else, including the tips seen between the arm and
the body, is back. The mass is the whole silhouette and is drawn behind the
body; the front piece is drawn over it.

**Onto our body.** The reference's head fits ours at the face-width
calibration (D0's, `harness/detail/baseline.py`): the two hairs agree within
0.1 to 0.2 head radii a side down to the jaw. Its body does not: its head is
far smaller against the body, so below the shoulders both its width and its
length are about twice ours in head radii. So y is as traced down to the
cheek, maps the reference's chin onto ours, and below the chin runs at one
scale, the body's (our shoulder to waist over theirs, 0.483); x scales about
the centre line by the same, easing from 1 at the cheek to it at the
reference's shoulder: locally the same scale both ways below the shoulder,
which is the skill's rule, and as traced on the head. A first round also
mapped the reference's shoulder onto ours, which squeezed its 0.57 head radii
of neck into our 0.12; the second round dropped that knot.

**Seen on our figure (`preview.py`, both rounds):** the fringe, the parting
and the side curtains read as the reference's; below the jaw the hair flares
over the shoulders into a hood, because on the reference's long body that
flare sits on broad shoulders and on ours right under a big head; the front
locks come out as short hooks on the shoulders; and the reference's own
interior lines (16 found) read as scratches, as ours did.

Writes `out/trace_hair/hair.json` (the fitted chains, in our head radii) and
`out/trace_hair/overlay.png` (the reference warped onto our frame, the chains
over it).

**`--as-is`** (the owner, 2026-09-29): no mapping at all, the reference's hair
in its own head radii at the face-width calibration, the gaps still filled;
to be put on Katherina at the tallest height and adjusted from there. Writes
`hair_asis.json` and `overlay_asis.png`. Its gaps come from `fill.py`
(interpolated along the hair's fall, the crown extrapolated), not from the
stand-ins below, which only the mapped trace still uses.
"""

import json
import sys

sys.path.insert(0, "harness/detail")
sys.path.insert(0, ".claude/skills/trace-reference")

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
from scipy import ndimage as ndi

import baseline
import trace_lib as tl
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
DIR = "ref-local/katherina_grok_real/segments"
OUT = "out/trace_hair"
AS_IS = "--as-is" in sys.argv
TAG = "_asis" if AS_IS else ""
PX = 100
BOX = (-2.6, -1.6, 2.6, 4.8) if AS_IS else (-2.2, -1.6, 2.2, 3.2)
# In the reference's head radii.
SPLIT = 2.05
FRONT_X = 1.3
CHEEK = 0.6
# Where x has eased all the way to the body's scale, in the reference's head
# radii: its shoulder.
X_EASE = 1.8
# Smoothing of the warped masks before the fit, in our pixels (PX per head
# radius): the cut's edge carries antialiasing noise the fit otherwise keeps.
SMOOTH = 1 if "--as-is" in sys.argv else 3
# The reference's outline is about 4 px; the cut is fill only, so grow by half.
GROW = 2


def seg(name, at, shape):
    s = np.asarray(Image.open(f"{DIR}/{name}.png").convert("RGBA"))[..., 3] > 128
    m = np.zeros(shape, bool)
    m[at[1] : at[1] + s.shape[0], at[0] : at[0] + s.shape[1]] = s
    return m


# The reference's shoulder line, read by eye off the brightened crop: the
# jacket's top beside the collar at 1.71, the arm's top at 1.92. A colour
# rule for the navy also takes the dark back hair beside the neck, so it is not
# measured.
REF_SHOULDER = 1.80


def ref_landmarks(a, ox, oy, s, chin_px):
    """The reference's chin, shoulder and waist in its head radii, the waist
    as the belt's centre row half a head radius left of the centre line (the
    buckle is at the centre)."""
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    brown = (R > 34) & (R < 70) & (R > G) & (G > B) & (R - B > 7)
    col = int(ox - 0.5 * s)
    lo, hi = int(oy + 3 * s), int(oy + 5 * s)
    rows = np.nonzero(brown[lo:hi, col])[0] + lo
    waist = ((rows.min() + rows.max()) / 2 - oy) / s
    return (chin_px - oy) / s, REF_SHOULDER, waist


AS_IS_HEIGHT = 1.3


def katherina_belt(height: float) -> float:
    """Katherina's belt's centre row in head radii below the head centre, off a
    render: the belt colour's lowest run down a column 0.35 head radii left of
    the centre line (clear of the buckle)."""
    import dataclasses
    import io

    import cairosvg

    p = dataclasses.replace(PRESETS["katherina"], height=height)
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=2))).convert("RGB")).astype(int)
    col = p.outfit.belt_color.lstrip("#")
    bc = np.array([int(col[i : i + 2], 16) for i in (0, 2, 4)])
    rows = np.nonzero(np.abs(im[:, int((sk.head_cx - 0.35 * sk.head_r) * 2)] - bc).sum(1) < 25)[0]
    run = np.split(rows, np.nonzero(np.diff(rows) > 1)[0] + 1)[-1]
    return float(((run.min() + run.max()) / 2 - sk.head_cy * 2) / (sk.head_r * 2))


def make_warp(ref_knots, our_knots):
    rk, ok = np.array(ref_knots), np.array(our_knots)
    body_slope = (ok[-1] - ok[-2]) / (rk[-1] - rk[-2])

    def ymap(y):
        y = np.asarray(y, float)
        out = np.interp(y, rk, ok)
        out = np.where(y < rk[0], y, out)
        return np.where(y > rk[-1], ok[-1] + (y - rk[-1]) * body_slope, out)

    def yinv(Y):
        Y = np.asarray(Y, float)
        out = np.interp(Y, ok, rk)
        out = np.where(Y < ok[0], Y, out)
        return np.where(Y > ok[-1], rk[-1] + (Y - ok[-1]) / body_slope, out)

    def xs(y):
        t = np.clip((np.asarray(y, float) - rk[0]) / (X_EASE - rk[0]), 0, 1)
        e = t * t * (3 - 2 * t)
        return 1 + (body_slope - 1) * e

    return ymap, yinv, xs, body_slope


def hull_fill(m):
    """`m` with its convex hull filled in (the hidden back hair behind the body)."""
    ys, xs = np.nonzero(m)
    if len(xs) < 3:
        return m
    from scipy.spatial import ConvexHull

    pts = np.stack([xs, ys], 1)
    h = ConvexHull(pts)
    poly = [tuple(map(float, pts[i])) for i in h.vertices]
    im = Image.new("1", (m.shape[1], m.shape[0]), 0)
    ImageDraw.Draw(im).polygon(poly, fill=1)
    return m | np.asarray(im, bool)


def main() -> None:
    a = np.asarray(Image.open(REF).convert("RGB")).astype(int)
    shape = a.shape[:2]
    locs = json.load(open(f"{OUT}/segments.json"))
    hair = seg("purple-hair", locs["purple-hair"]["at"], shape)
    hat = seg("witch-hat", locs["witch-hat"]["at"], shape)
    bat = seg("black-bat", locs["black-bat"]["at"], shape)
    lines: list[str] = []
    ox, oy, s = baseline.calibrate(lines)
    print("\n".join(lines))
    face = baseline.face_component(a, baseline.REF_CHEEK)
    chin_px = baseline.widest_and_chin(face)[3]

    Y, X = np.mgrid[0 : shape[0], 0 : shape[1]]
    hx, hy = (X - ox) / s, (Y - oy) / s

    # Interior ink (before growing): dark inside the hair, off its edge.
    ink = ndi.binary_erosion(hair, iterations=3) & (a.sum(2) <= 120)

    m = ndi.binary_dilation(hair, iterations=GROW)
    # The bat: the left side mirrored, inside the bat only.
    mx = np.clip((2 * ox - X).round().astype(int), 0, shape[1] - 1)
    mirrored = m[Y, mx]
    m |= bat & mirrored
    # The crown: a circle about the centre line fitted to the outer edge.
    edge_pts = []
    for yy in range(int(oy - 1.0 * s), int(oy + 0.3 * s)):
        row = np.nonzero(m[yy])[0]
        if len(row):
            edge_pts += [(row.min(), yy), (row.max(), yy)]
    e = np.array(edge_pts, float)
    # (x - ox)^2 + (y - cy)^2 = R^2, linear in cy and R^2 - cy^2.
    A = np.stack([2 * e[:, 1], np.ones(len(e))], 1)
    b = (e[:, 0] - ox) ** 2 + e[:, 1] ** 2
    (cy_c, k), *_ = np.linalg.lstsq(A, b, rcond=None)
    R = np.sqrt(k + cy_c**2)
    print(f"crown circle: centre y {(cy_c - oy) / s:+.3f}, radius {R / s:.3f} head radii")
    crown = ((X - ox) ** 2 + (Y - cy_c) ** 2 <= R**2) & hat & (hy < 0)
    m |= crown

    split = int(oy + SPLIT * s)
    below = m.copy()
    below[:split] = False
    lab, n = ndi.label(below)
    front = m.copy()
    front[split:] = False
    back_parts = np.zeros_like(m)
    for i in range(1, n + 1):
        k = lab == i
        if k.sum() < 150:
            continue
        ys, xs_ = np.nonzero(k)
        cxh = (xs_.mean() - ox) / s
        if ys.min() <= split + 1 and abs(cxh) < FRONT_X:
            front |= k
        else:
            back_parts |= k
    mass = m.copy()
    for side in (-1, 1):
        half = back_parts & ((X - ox) * side > 0)
        joined = half | (m & (Y >= split - 2) & (Y < split + 6) & ((X - ox) * side > 0))
        mass |= hull_fill(joined)
    # The head's rows: everything between the outermost hair is hair.
    for yy in range(0, split):
        row = np.nonzero(m[yy])[0]
        if len(row):
            mass[yy, row.min() : row.max() + 1] = True
    mass = ndi.binary_fill_holes(mass)
    if AS_IS:
        # `fill.py`'s interpolated and extrapolated masks replace the stand-ins
        # above (circle, mirror, hulls) for the as-is trace.
        filled = np.load(f"{OUT}/filled.npz")
        front = filled["front"]
        # No hole filling: the page seen between a back sheet and the arm is a
        # hole in the hair, drawn as one (`parts`).
        mass = filled["back"] | front

    # Onto our body.
    p = PRESETS["katherina"]
    sk = c.skeleton_for(p)
    r = sk.head_r
    our_chin = float(lines[0].split("chin ")[1])
    ref_chin, ref_sh, ref_wa = ref_landmarks(a, ox, oy, s, chin_px)
    our_sh, our_wa = (sk.shoulder_y - sk.head_cy) / r, (sk.waist_y - sk.head_cy) / r
    print(f"landmarks (ref -> ours): chin {ref_chin:.3f} -> {our_chin:.3f}, shoulder {ref_sh:.3f} -> {our_sh:.3f}, waist {ref_wa:.3f} -> {our_wa:.3f}")
    # Round two: no knot at the shoulder. Mapping the reference's shoulder
    # onto ours squeezed its 0.57 head radii of neck into our 0.12 and packed
    # the flare over its shoulders under the jaw, a hood. Below the chin one
    # scale, the body's (shoulder to waist), so the hair hangs over our
    # shoulders a little lower than theirs sit.
    slope = (our_wa - our_sh) / (ref_wa - ref_sh)
    far = ref_wa + 1.0
    ymap, yinv, xs, slope = make_warp(
        [CHEEK, ref_chin, far - 0.5, far], [CHEEK, our_chin, our_chin + (far - 0.5 - ref_chin) * slope, our_chin + (far - ref_chin) * slope]
    )
    print(f"body scale below the chin: {slope:.3f}")
    if AS_IS:
        # Shortened by the belt (the owner, 2026-09-29): as traced down to the
        # cheek, then one linear squeeze in y so the reference's belt lands on
        # Katherina's at the tallest height. Widths stay as traced.
        our_belt = katherina_belt(AS_IS_HEIGHT)
        k = (our_belt - CHEEK) / (ref_wa - CHEEK)
        print(f"as-is: belt {ref_wa:.3f} -> {our_belt:.3f} at height {AS_IS_HEIGHT}, y below the cheek x {k:.3f}")

        def ymap(y):
            y = np.asarray(y, float)
            return np.where(y > CHEEK, CHEEK + (y - CHEEK) * k, y)

        def yinv(Y):
            Y = np.asarray(Y, float)
            return np.where(Y > CHEEK, CHEEK + (Y - CHEEK) / k, Y)

        def xs(y):
            return np.ones_like(np.asarray(y, float))

    w, h = int((BOX[2] - BOX[0]) * PX), int((BOX[3] - BOX[1]) * PX)
    gy, gx = np.mgrid[0:h, 0:w]
    ux, uy = gx / PX + BOX[0], gy / PX + BOX[1]
    ry = yinv(uy)
    rx = ux / xs(ry)
    px_, py_ = (ox + rx * s).round().astype(int), (oy + ry * s).round().astype(int)
    ok = (px_ >= 0) & (px_ < shape[1]) & (py_ >= 0) & (py_ < shape[0])
    px_, py_ = np.clip(px_, 0, shape[1] - 1), np.clip(py_, 0, shape[0] - 1)

    def warp(mm):
        return mm[py_, px_] & ok

    def to_units(pts):
        return [(x / PX + BOX[0], y / PX + BOX[1]) for x, y in pts]

    def smooth(mm):
        disk = np.hypot(*np.mgrid[-SMOOTH : SMOOTH + 1, -SMOOTH : SMOOTH + 1]) <= SMOOTH
        return ndi.binary_opening(ndi.binary_closing(mm, disk), disk)

    W_mass = smooth(warp(mass)) if AS_IS else ndi.binary_fill_holes(smooth(warp(mass)))
    W_front = smooth(warp(front)) & W_mass

    def parts(mm, tol, min_px=60):
        """Each connected piece's outer contour and its holes, fitted: the
        as-is trace keeps the page it saw inside and between the hair."""
        out = []
        lab_p, n_p = ndi.label(mm)
        for i in range(1, n_p + 1):
            piece = lab_p == i
            if piece.sum() < min_px:
                continue
            outer = tl.fit_closed(to_units(tl.boundary(piece)), tol)
            holes = []
            hl, nh = ndi.label(ndi.binary_fill_holes(piece) & ~piece)
            for j in range(1, nh + 1):
                hole = hl == j
                if hole.sum() >= min_px:
                    holes.append(tl.fit_closed(to_units(tl.boundary(hole)), tol))
            out.append([outer, holes])
        return out

    mass_parts = parts(W_mass, 0.012) if AS_IS else []
    front_parts = parts(W_front, 0.010) if AS_IS else []
    if AS_IS:
        print(f"parts: mass {len(mass_parts)} pieces, {sum(len(h) for _, h in mass_parts)} holes; front {len(front_parts)} pieces, {sum(len(h) for _, h in front_parts)} holes")
        W_mass = ndi.binary_fill_holes(W_mass)
    mb, fb = tl.boundary(W_mass), tl.boundary(W_front)
    print(f"boundaries: mass {len(mb)} px, front {len(fb)} px", flush=True)
    mass_chain = tl.fit_closed(to_units(mb), 0.012 if AS_IS else 0.02)
    front_chain = tl.fit_closed(to_units(fb), 0.010 if AS_IS else 0.015)

    # The front's edges that are drawn: all of its boundary but the cut across
    # the back hair at the split row, which is inside the mass.
    split_u = float(ymap(SPLIT))
    inner = ndi.binary_erosion(W_mass, iterations=3)
    keep = [not (abs((y / PX + BOX[1]) - split_u) < 0.03 and inner[y, x]) for x, y in fb]
    runs, cur = [], []
    for pt, kp in zip(fb, keep):
        if kp:
            cur.append(pt)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        if runs and keep[0]:
            runs[0] = cur + runs[0]
        else:
            runs.append(cur)
    front_edges = []
    for run in runs:
        if len(run) < 8:
            continue
        u = to_units(run)
        front_edges.append(tl.fit_chain(u, tl.simplify(u, 0.015)))

    # Interior lines, in the reference's pixels, then mapped forward.
    lab, n = ndi.label(ink, structure=np.ones((3, 3)))
    strands = []
    for i in range(1, n + 1):
        ys, xs_ = np.nonzero(lab == i)
        if len(xs_) < 25:
            continue
        ry_, rx_ = (ys - oy) / s, (xs_ - ox) / s
        uy_ = ymap(ry_)
        ux_ = rx_ * xs(ry_)
        pts = np.stack([ux_, uy_], 1)
        cc = pts.mean(0)
        _u, _s, vt = np.linalg.svd(pts - cc)
        t = (pts - cc) @ vt[0]
        order = np.argsort(t)
        nb = max(2, min(10, len(order) // 12))
        centre = [tuple(map(float, pts[bb].mean(0))) for bb in np.array_split(order, nb) if len(bb)]
        if np.hypot(*np.subtract(centre[-1], centre[0])) < 0.08:
            continue
        mid = centre[len(centre) // 2]
        gx_i, gy_i = int((mid[0] - BOX[0]) * PX), int((mid[1] - BOX[1]) * PX)
        in_front = bool(0 <= gy_i < h and 0 <= gx_i < w and W_front[gy_i, gx_i])
        strands.append({"chain": tl.fit_chain(centre, tl.simplify(centre, 0.01)), "front": in_front})
    print(f"mass {len(mass_chain[1])} segments, front {len(front_chain[1])}, front edges {len(front_edges)}, strands {len(strands)}")

    lines_mapped = []
    if AS_IS:
        # `lines.py`'s chains are in the reference's head radii; they take the
        # same squeeze (applied to the control points too, exact on either side
        # of the cheek line).
        def mp(q):
            return (float(q[0]), float(ymap(q[1])))

        for s0, segs in json.load(open(f"{OUT}/lines.json"))["lines"]:
            lines_mapped.append((mp(s0), [(mp(cq), mp(e)) for cq, e in segs]))
    json.dump(
        {
            "lines": lines_mapped,
            "squeeze": float(k) if AS_IS else None,
            "cheek": CHEEK,
            "mass_parts": mass_parts,
            "front_parts": front_parts,
            "mass": mass_chain,
            "front": front_chain,
            "front_edges": front_edges,
            "strands": strands,
            "calibration": {"origin": [ox, oy], "px_per_r": s},
            "landmarks": {"ref": [CHEEK, ref_chin, ref_sh, ref_wa], "ours": [CHEEK, our_chin, our_sh, our_wa]},
        },
        open(f"{OUT}/hair{TAG}.json", "w"),
        indent=1,
    )

    # The overlay: the reference warped into our frame, brightened, chains on it.
    rgb = a[py_, px_].astype(np.uint8)
    rgb[~ok] = 0
    im = ImageEnhance.Brightness(Image.fromarray(rgb)).enhance(2.5).resize((w * 2, h * 2), Image.LANCZOS)
    d = ImageDraw.Draw(im)

    def P(q):
        return ((q[0] - BOX[0]) * PX * 2, (q[1] - BOX[1]) * PX * 2)

    for chain, col in ((mass_chain, (0, 255, 0)), (front_chain, (255, 60, 60))):
        d.line([P(q) for q in tl.sample_chain(*chain)], fill=col, width=2)
    for chain in front_edges:
        d.line([P(q) for q in tl.sample_chain(*chain)], fill=(255, 220, 0), width=2)
    for st in strands:
        d.line([P(q) for q in tl.sample_chain(*st["chain"])], fill=(0, 200, 255) if st["front"] else (255, 0, 255), width=2)
    im.save(f"{OUT}/overlay{TAG}.png")


if __name__ == "__main__":
    main()
