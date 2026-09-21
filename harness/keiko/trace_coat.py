"""Trace Keiko's lab coat off `ref-local/keiko-tall-chibi/segments/white-lab-coat.png`.

Method: `.claude/skills/trace-reference/SKILL.md`, the same pipeline
`harness/clothes/trace_cut.py` used for Katherina's jacket. Two things differ
here and both are recorded in `docs/keiko-clothes-plan.md`:

**The reference is not the cut frame.** Katherina's reference *is*
`tall_chibi`, the body `_garment_placement` maps cuts from, so her traced head
radii were already cut coordinates. Keiko's reference stands 3.68 heads
against `tall_chibi`'s 3.47, so every y is rescaled about the chin by
`(5.940 - 1) / (sole - 1)` before it is emitted, and x is left alone. Widths
carry across untouched because they already agree: the reference's collar sits
at 0.276 head radii and `tall_chibi`'s neck at 0.280. Normalising the figure's
length this way is also what makes the cut independent of the calibration,
which is an estimate: whatever the true head radius is, the coat keeps its
proportions against the figure it was drawn on.

**The crop is occlusion-cut**, so the belt is missing out of the coat as a
horizontal band about 39 px deep. It is bridged by a closing that works
vertically only: a square structuring element would close the coat's front
opening with it, which is the one feature this milestone is about.

Writes `out/keiko/coat_trace.json` and `out/keiko/coat_overlay.png`; look at
the overlay before trusting any of it.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".claude/skills/trace-reference"))
import trace_lib as tl  # noqa: E402

BASE = "ref-local/keiko-tall-chibi"
OUT = Path("out/keiko")
COAT_AT = (398, 530)  # the crop's top-left in the composite, (x, y)
OX, OY, R = 625.5, 394.0, 177.5  # `landmarks.py` re-derives these
HALF_STROKE = 2  # half the reference's outline width, in pixels
REF_SOLE = 6.361  # the reference figure's sole, in its own head radii
CUT_SOLE = 5.940  # `tall_chibi`'s, the frame cuts are emitted in
SQUASH = (CUT_SOLE - 1.0) / (REF_SOLE - 1.0)

arr = np.asarray(Image.open(f"{BASE}/keiko-tall-chibi.png").convert("RGBA")).astype(int)
a = arr[:, :, 3:4] / 255.0
rgb = (arr[:, :, :3] * a + 255 * (1 - a)).astype(int)
H, W = rgb.shape[:2]

seg = np.asarray(Image.open(f"{BASE}/segments/white-lab-coat.png").convert("RGBA")).astype(int)
sh, sw = seg.shape[:2]
coat = np.zeros((H, W), bool)
coat[COAT_AT[1] : COAT_AT[1] + sh, COAT_AT[0] : COAT_AT[0] + sw] = seg[:, :, 3] > 128
disk = ndi.generate_binary_structure(2, 1)


def grow(m, n):
    return ndi.binary_dilation(m, structure=disk, iterations=n) if n else m


def hy(y):
    return (y - OY) / R


def hx(x):
    return (x - OX) / R


# --- the pieces, as the reference's own fill regions -------------------------
fill = coat & (rgb.sum(2) > 300)
lab, n = ndi.label(fill)
pieces = {"lapel": [], "panel": [], "cuff": []}
for i in range(1, n + 1):
    m = lab == i
    if m.sum() < 1000:
        continue
    ys, xs = np.nonzero(m)
    top, bot, w = hy(ys.min()), hy(ys.max()), (xs.max() - xs.min()) / R
    # The lapel facings start at the collar's tip and stop above the belt; the
    # cuffs are the short bands at the sleeve's end; everything else is panel.
    if top < 0.9 and bot < 2.6:
        pieces["lapel"].append(i)
    elif top > 3.0 and w < 0.6:
        pieces["cuff"].append(i)
    else:
        pieces["panel"].append(i)
print({k: v for k, v in pieces.items()})

# The belt is cut out of the crop. Bridge it vertically only: a square element
# would close the coat's front opening, which is the feature being traced.
VERT = np.ones((49, 1), bool)
whole = ndi.binary_closing(coat, structure=VERT)
whole = ndi.binary_fill_holes(whole)


def tidy(m, clip=True):
    m = ndi.binary_closing(grow(m, 3), structure=disk, iterations=3)
    m = ndi.binary_fill_holes(m)
    lb, ln = ndi.label(m)
    if ln > 1:  # keep the largest piece; specks come from the outline's antialiasing
        m = lb == (np.argmax(ndi.sum(m, lb, range(1, ln + 1))) + 1)
    # `clip=False` for a piece whose occlusion is being undone: `whole` is the
    # crop's own alpha, so intersecting with it puts the hand's bite straight
    # back into the skirt panel.
    return m & whole if clip else m


def side_mask(ids, side, bridge=True):
    """One piece of the coat on one side.

    `bridge=False` for a piece the belt does not cross. The vertical closing
    that bridges the belt's cut also fills any notch cut in from the side, and
    the lapel's notch is exactly that: the facing ends at y 2.29, well above the
    belt, so it never needed bridging, and with it the notch was closed up and
    the facing traced as a plain wedge (`docs/keiko-clothes-plan.md`, P3).
    """
    m = np.isin(lab, ids) & ((np.arange(W)[None, :] - OX) * side > 0)
    if bridge:
        m = ndi.binary_closing(m, structure=VERT)
    return tidy(m)


def split_panel_and_sleeve(side):
    """The body panel and the sleeve, which the reference draws as one fill.

    Below the armpit the arm's own outline already divides them, so each row
    holds two runs of coat: the panel nearer the centre line and the sleeve
    outside it. Above the armpit there is one run, the shoulder, and it belongs
    to the panel; the sleeve's own top is a disc about the joint that
    `_sleeve_placement` makes, so nothing up there needs tracing.
    """
    m = np.isin(lab, pieces["panel"]) & ((np.arange(W)[None, :] - OX) * side > 0)
    m = ndi.binary_closing(m, structure=VERT)
    panel = np.zeros_like(m)
    sleeve = np.zeros_like(m)
    for y in np.nonzero(m.any(1))[0]:
        xs = np.nonzero(m[y])[0]
        runs = np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)
        runs = [r for r in runs if len(r) > 3]
        if not runs:
            continue
        runs.sort(key=lambda r: abs(r.mean() - OX))
        panel[y, runs[0]] = True
        for r in runs[1:]:
            sleeve[y, r] = True
    return unbite(tidy(panel, clip=False), side), tidy(sleeve)


def unbite(panel, side):
    """Undo the hand's bite out of the skirt panel's outer edge.

    The crop is occlusion-cut, so where the reference's hand hangs over the
    coat the panel is missing a hand-shaped notch, with a sliver of coat still
    showing outside it. Our hand is not in the reference's place, so a traced
    notch would leave a gap beside our own hand instead of fitting round it.

    Bridging horizontally across those rows is the whole fix: it closes the
    hand and nothing else, because the sleeve has already ended at its cuff
    above them, so there is no other gap on this side to close. Carrying the
    widest edge seen so far down the panel was tried first and over-corrected,
    picking up the sleeve's outer edge where the runs merge and carrying it
    down past the hem as a straight line outside the coat.
    """
    ys, xs = np.nonzero(panel)
    band = slice(int(OY + 3.72 * R), min(int(OY + 4.35 * R), panel.shape[0]))
    wide = np.ones((1, int(0.40 * R)), bool)
    panel[band] = ndi.binary_closing(panel[band], structure=wide)
    return panel


def local(pts):
    """Reference pixels -> cut coordinates: head radii, squashed about the chin."""
    out = []
    for x, y in pts:
        u, v = hx(x), hy(y)
        out.append((u, 1.0 + (v - 1.0) * SQUASH))
    return out


def trace(mask, tol):
    start, segs = tl.fit_closed(local(tl.boundary(grow(mask, HALF_STROKE))), tol)
    return {"start": start, "segs": segs}


def interior_lines(side):
    """The lapel's fold and notch, which are line work rather than silhouette.

    The reference draws the collar band and the lapel facing as one fill, so the
    step between them, the notch, never reaches the component's boundary: it is
    ink *inside* the region. Traced as part of the closed contour it is simply
    smoothed away, which is why the first pass produced a lapel with no notch in
    it at all and read plain (`docs/keiko-clothes-plan.md`, P3).

    Method is the skill's interior-line case: erode the region's hull past the
    outline's own width, take the dark pixels left inside it, drop specks, order
    each stroke along its principal axis and fit an open chain.
    """
    hull = ndi.binary_fill_holes(side_mask(pieces["lapel"], side, bridge=False))
    inner = ndi.binary_erosion(hull, structure=disk, iterations=HALF_STROKE + 2)
    dark = inner & (rgb.sum(2) < 200)
    lab_, n_ = ndi.label(dark, structure=np.ones((3, 3), bool))
    out = []
    for i in range(1, n_ + 1):
        m = lab_ == i
        if m.sum() < 25:
            continue
        ys_, xs_ = np.nonzero(m)
        pts = np.stack([xs_, ys_], 1).astype(float)
        c0 = pts.mean(0)
        _, _, vt = np.linalg.svd(pts - c0, full_matrices=False)
        t = (pts - c0) @ vt[0]
        order = np.argsort(t)
        # Average along the stroke in bins, which is its centre line; the raw
        # pixels are a few wide and zigzag at this line weight.
        bins = np.array_split(order, min(8, max(2, len(order) // 12)))
        centre = [pts[b].mean(0) for b in bins if len(b)]
        loc = local([(q[0], q[1]) for q in centre])
        keep = tl.simplify(loc, 0.010)
        if len(keep) < 3:
            continue
        start, segs = tl.fit_chain(loc, keep)
        # The hull was eroded past the outline's width to find this ink, so both
        # ends stop short of the edges the stroke actually runs between and it
        # floats in the middle of the facing. Carry each end back out along its
        # own direction by that much again; the overshoot hides under the
        # outline it meets.
        ext = (HALF_STROKE + 11) / R

        def carried(pt, toward):
            dx, dy = pt[0] - toward[0], pt[1] - toward[1]
            n = (dx * dx + dy * dy) ** 0.5 or 1.0
            return (pt[0] + dx / n * ext, pt[1] + dy / n * ext)

        start = carried(start, segs[0][0])
        segs = list(segs)
        segs[-1] = (segs[-1][0], carried(segs[-1][1], segs[-1][0]))
        out.append({"start": start, "segs": segs})
    return out


shapes = {}
lines = {}
land = {}
for side, name in ((-1, "left"), (1, "right")):
    panel, sleeve = split_panel_and_sleeve(side)
    cuff = side_mask(pieces["cuff"], side)
    shapes[f"panel_{name}"] = trace(panel, 0.012)
    shapes[f"lapel_{name}"] = trace(side_mask(pieces["lapel"], side, bridge=False), 0.006)
    shapes[f"sleeve_{name}"] = trace(sleeve, 0.012)
    shapes[f"cuff_{name}"] = trace(cuff, 0.010)
    lines[name] = interior_lines(side)
    # The sleeve's landmarks, for `SleeveCut`: the shoulder joint is the centre
    # of the sleeve's topmost rows, the wrist the cuff's bottom centre.
    sy, sx = np.nonzero(sleeve)
    topmost = sx[sy < sy.min() + 12]
    cy_, cx_ = np.nonzero(cuff)
    bottom = cx_[cy_ > cy_.max() - 6]
    land[name] = {
        "pivot": [float(hx(topmost.mean())), 1.0 + (hy(sy.min()) - 1.0) * SQUASH],
        "wrist": [float(hx(bottom.mean())), 1.0 + (hy(cy_.max()) - 1.0) * SQUASH],
    }
for k, v in shapes.items():
    print(f"{k:14s} {len(v['segs']):3d} segments")
print("interior lines", {k: len(v) for k, v in lines.items()})
print("sleeve landmarks", land)

colours = {}
for name, ids in (("coat", pieces["panel"]),):
    m = ndi.binary_erosion(np.isin(lab, ids), iterations=3)
    colours[name] = "#%02x%02x%02x" % tuple(int(v) for v in np.median(rgb[m], axis=0))
print(colours, "squash %.4f" % SQUASH)

OUT.mkdir(parents=True, exist_ok=True)
json.dump({"shapes": shapes, "lines": lines, "landmarks": land, "colours": colours, "squash": SQUASH}, open(OUT / "coat_trace.json", "w"))

# --- overlay: the fitted chains back over the reference, to be looked at -----
S = 2
img = Image.fromarray(np.clip(rgb * 1.0, 0, 255).astype("uint8")).resize((W * S, H * S), Image.NEAREST)
d = ImageDraw.Draw(img)
palette = ["#ff0000", "#00aa00", "#0000ff", "#ff00ff", "#ff8800", "#00cccc", "#8800ff", "#888800"]
for i, (name, ch) in enumerate(shapes.items()):
    pts = tl.sample_chain(ch["start"], ch["segs"], 10)
    xy = [((u * R + OX) * S, ((v - 1.0) / SQUASH + 1.0) * R * S + OY * S) for u, v in pts]
    d.line(xy, fill=palette[i % len(palette)], width=2)
img.crop((int(380 * S), int(500 * S), int(880 * S), int(1440 * S))).save(OUT / "coat_overlay.png")
print("overlay written")
