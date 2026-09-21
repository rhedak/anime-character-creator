"""Keiko's clothes landmarks, measured off `ref-local/keiko-tall-chibi/`
(`docs/keiko-clothes-plan.md`, K0).

Calibration is this repo's accepted estimate, the same one
`harness/body/satoshi_tall_chibi_landmarks.py` uses and flags: the widest row
of face skin is the head's widest point, which gives both the radius and the
vertical centre. Two alternatives were tried and rejected in K0 and are
recorded in the plan doc's calibration section, so they are not tried again:
the equator-to-chin run (contaminated, the skin component runs on down the
neck to whatever garment cuts it) and a circle fit to the jaw arc (the jaw in
this style is not a circular arc; it returns R = 141.8 on Satoshi's composite
against his known-good 171.5).

Unlike the grok layer exports, the three garment segments here are true pixel
crops of the composite, so their alpha is each garment's own extent, including
where the composite's other layers sit on top of it. `locate` re-checks that
every run: a crop matches at a mean RGB difference under 0.1, a regenerated
variant does not match at all.

Prints every number the plan doc's table quotes, so the table has a runnable
source.
"""

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

BASE = "ref-local/keiko-tall-chibi"
REF = f"{BASE}/keiko-tall-chibi.png"

im = Image.open(REF).convert("RGBA")
arr = np.asarray(im).astype(int)
alpha = arr[:, :, 3:4] / 255.0
white = np.full(arr.shape[:2] + (3,), 255)
rgb = (arr[:, :, :3] * alpha + white * (1 - alpha)).astype(int)
H, W = rgb.shape[:2]


def mask_rgb(col, tol=14):
    return np.abs(rgb - np.array(col)).sum(2) <= tol


# --- head calibration -------------------------------------------------------
# The face's own y range, above the collar and well below the crown, so the
# hands (a near-identical skin colour) and the hair parting cannot win the
# widest row.
skin_seed = rgb[380, 626]
skin = mask_rgb(skin_seed, 40)
skin[:200, :] = False
skin[560:, :] = False
lab, n = ndi.label(skin)
face = lab == (np.argmax(ndi.sum(skin, lab, range(1, n + 1))) + 1)
rows = [(y, xs.min(), xs.max()) for y in range(H) if len(xs := np.nonzero(face[y])[0])]
# The widest row is a plateau about 45 px deep here, so the single argmax row
# moves with the colour tolerance. Take the plateau's median row instead: the
# radius is unaffected and the centre stops sliding by 0.06 head radii.
widest = max(r[2] - r[1] for r in rows)
plateau = [r for r in rows if r[2] - r[1] >= widest - 2]
y0 = int(np.median([r[0] for r in plateau]))
x0, x1 = min(r[1] for r in plateau), max(r[2] for r in plateau)
OX, OY, R = (x0 + x1) / 2, float(y0), (x1 - x0) / 2
print(f"widest-row plateau: y {plateau[0][0]} to {plateau[-1][0]}, {len(plateau)} rows")
print(f"skin colour sampled {tuple(skin_seed)}")
print(f"head calibration: centre ({OX:.1f}, {OY:.1f}), r = {R:.1f} px")

ys_a, xs_a = np.nonzero(arr[:, :, 3] > 128)
sole = (ys_a.max() - OY) / R
print(f"figure: crown {(ys_a.min() - OY) / R:+.3f} hr, sole {sole:+.3f} hr, {(1 + sole) / 2:.3f} heads")
print("  (our tall_chibi_long_torso computes 3.245 heads; the plan's K7 keeps this a body question)")


def hy(y):
    return (y - OY) / R


def hx(x):
    return (x - OX) / R


# --- the garment segments, each checked as a true crop ----------------------
def locate(name, guess, span=6):
    seg = np.asarray(Image.open(f"{BASE}/segments/{name}").convert("RGBA")).astype(int)
    sh, sw = seg.shape[:2]
    m = seg[:, :, 3] > 200
    best = None
    for oy in range(guess[1] - span, guess[1] + span + 1):
        for ox in range(guess[0] - span, guess[0] + span + 1):
            d = np.abs(rgb[oy : oy + sh, ox : ox + sw] - seg[:, :, :3]).sum(2)[m].mean() / 3
            if best is None or d < best[0]:
                best = (d, ox, oy)
    d, ox, oy = best
    full = np.zeros((H, W), bool)
    full[oy : oy + sh, ox : ox + sw] = seg[:, :, 3] > 128
    col = np.zeros((H, W, 3), int)
    col[oy : oy + sh, ox : ox + sw] = seg[:, :, :3]
    print(f"{name:24s} crop at ({ox}, {oy}), mean RGB difference {d:.3f}")
    return full, col


print()
# Offsets are (x, y) of the crop's top-left corner in the composite.
coat, coat_rgb = locate("white-lab-coat.png", (398, 530))
dress, dress_rgb = locate("dark-gray-dress.png", (564, 540))
belt, belt_rgb = locate("belt-with-buckle.png", (509, 839))


def extent(mask, y):
    xs = np.nonzero(mask[y])[0]
    return (xs.min(), xs.max()) if len(xs) else None


def half_w(mask, y):
    e = extent(mask, y)
    return None if e is None else (e[1] - e[0]) / 2 / R


def hexc(mask, n=2):
    inner = ndi.binary_erosion(mask, iterations=n)
    px = rgb[inner if inner.any() else mask]
    return "#%02x%02x%02x" % tuple(int(v) for v in np.median(px, axis=0))


# --- the coat ---------------------------------------------------------------
print("\ncoat")
cl, cn = ndi.label(coat)
parts = []
for i in range(1, cn + 1):
    m = cl == i
    if m.sum() < 400:
        continue
    ys, xs = np.nonzero(m)
    parts.append((m.sum(), i, hy(ys.min()), hy(ys.max()), hx(xs.min()), hx(xs.max())))
for size, i, t, b, l, r in sorted(parts, reverse=True):
    print(f"  part {i:2d}  {size:6d}px  y {t:+.3f} to {b:+.3f}   x {l:+.3f} to {r:+.3f}")

coat_ys = np.nonzero(coat.any(1))[0]
prof = [(hy(y), half_w(coat, y)) for y in coat_ys]
top = max((w, y) for y, w in prof if y < 2.0)
print(f"  widest above the belt (shoulder): y {top[1]:+.3f}, half-width {top[0]:.3f}")
print(f"  hem: y {hy(coat_ys.max()):+.3f}")

# The opening between the two fronts: the run of not-coat that contains the
# centre line, between the coat's own left and right edges on that row.
#
# The crop is occlusion-cut, so the belt is missing out of the coat and every
# row it covers reads as one enormous gap. Those rows are skipped rather than
# measured: what the fronts do behind the belt is not visible in this
# reference, and a number taken there would be the belt's height, not the
# coat's opening.
b_lo, b_hi = np.nonzero(belt.any(1))[0][[0, -1]]
gaps = []
for y in coat_ys:
    if b_lo - 2 <= y <= b_hi + 2:
        continue
    e = extent(coat, y)
    if e is None or not (e[0] < OX < e[1]) or coat[y, int(round(OX))]:
        continue
    row = coat[y, e[0] : e[1] + 1]
    rl, rn = ndi.label(~row)
    g = rl[int(round(OX)) - e[0]]
    if g:
        gaps.append((hy(y), (rl == g).sum() / R))
if gaps:
    above = [g for g in gaps if g[0] < hy(b_lo)]
    below = [g for g in gaps if g[0] > hy(b_hi)]
    print(f"  fronts closest above the belt: y {min(above, key=lambda t: t[1])[0]:+.3f}, gap {min(above, key=lambda t: t[1])[1]:.3f} hr")
    print(f"  first row below the belt: y {below[0][0]:+.3f}, gap {below[0][1]:.3f} hr")
    for want in np.arange(1.0, 5.0, 0.25):
        near = min(gaps, key=lambda t: abs(t[0] - want))
        if abs(near[0] - want) < 0.08:
            print(f"    gap at y {near[0]:+.3f}: {near[1]:.3f} hr")
    for want in (2.9, 3.5, 4.0, 4.5):
        y = int(round(OY + want * R))
        w = half_w(coat, y)
        if w:
            print(f"    coat half-width at y {want:+.2f}: {w:.3f}  (an outer envelope: it includes the sleeve)")

# --- the dress --------------------------------------------------------------
print("\ndress")
dl, dn = ndi.label(dress)
for i in range(1, dn + 1):
    m = dl == i
    if m.sum() < 200:
        continue
    ys, xs = np.nonzero(m)
    print(f"  part {i:2d}  {m.sum():6d}px  y {hy(ys.min()):+.3f} to {hy(ys.max()):+.3f}   x {hx(xs.min()):+.3f} to {hx(xs.max()):+.3f}")
d_ys = np.nonzero(dress.any(1))[0]
print(f"  collar top: y {hy(d_ys.min()):+.3f}")
for want in (0.85, 0.95, 1.05, 1.20, 2.80, 3.40, 3.80, 4.40, 4.80):
    y = int(round(OY + want * R))
    w = half_w(dress, y)
    if w:
        print(f"    half-width at y {want:+.2f}: {w:.3f}")
# The hem: is the bottom edge a straight horizontal cut (a real hem) or ragged
# (the coat occluding it)? Print the last rows' own extents and decide by eye.
print(f"  lowest dress pixel: y {hy(d_ys.max()):+.3f}")
for y in range(d_ys.max() - 6, d_ys.max() + 1):
    e = extent(dress, y)
    if e:
        print(f"    row y {hy(y):+.3f}: x {hx(e[0]):+.3f} to {hx(e[1]):+.3f}")
legs = mask_rgb(skin_seed, 40)
legs[: int(OY + 4.5 * R), :] = False
if legs.any():
    ly = np.nonzero(legs.any(1))[0]
    print(f"  bare leg skin below the hem: y {hy(ly.min()):+.3f} to {hy(ly.max()):+.3f}")

# --- the belt ---------------------------------------------------------------
print("\nbelt")
b_ys = np.nonzero(belt.any(1))[0]
b_xs = np.nonzero(belt.any(0))[0]
print(f"  band: y {hy(b_ys.min()):+.3f} to {hy(b_ys.max()):+.3f}, centre {hy((b_ys.min() + b_ys.max()) / 2):+.3f}")
print(f"  x {hx(b_xs.min()):+.3f} to {hx(b_xs.max()):+.3f}")
heights = np.array([belt[:, x].sum() for x in range(W)]) / R
band = np.median(heights[b_xs][heights[b_xs] > 0])
print(f"  band thickness (median column): {band:.3f} hr")
tall = [x for x in b_xs if heights[x] > band * 1.12]
if tall:
    tl, tn = ndi.label(np.isin(np.arange(W), tall))
    for i in range(1, tn + 1):
        cols = np.nonzero(tl == i)[0]
        if len(cols) < 3:
            continue
        print(
            f"    taller than the band: x {hx(cols.min()):+.3f} to {hx(cols.max()):+.3f}"
            f"  ({(cols.max() - cols.min() + 1) / R:.3f} wide, up to {heights[cols].max():.3f} tall)"
        )
# The buckle: everything on the band that is neither its own near-white nor
# the outline. Taking "dark" alone picks up the band's outline all the way
# round, which is how the extent first came out as the whole belt.
pale = np.abs(rgb - np.array([236, 236, 236])).sum(2) <= 60
# ...and neither the outline, which rings the whole band and otherwise wins as
# the largest not-pale component. The buckle's frame is a mid tone (it sums to
# about 395 across the channels), the outline is near black (about 42).
metal = belt & ~pale & (rgb.sum(2) > 150)
ml, mn = ndi.label(metal)
if mn:
    keep = ml == (np.argmax(ndi.sum(metal, ml, range(1, mn + 1))) + 1)
    keep = ndi.binary_fill_holes(keep)
    ys, xs = np.nonzero(keep)
    print(
        f"  buckle: x {hx(xs.min()):+.3f} to {hx(xs.max()):+.3f}, y {hy(ys.min()):+.3f} to {hy(ys.max()):+.3f}"
        f"  ({(xs.max() - xs.min() + 1) / R:.3f} by {(ys.max() - ys.min() + 1) / R:.3f})"
    )
    # The frame is an open ring (the strap passes through it), so filling its
    # holes does not reach the dark centre. Take the darkest component inside
    # its bounding box instead.
    box = np.zeros_like(keep)
    box[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1] = True
    inner = box & (rgb.sum(2) < 120)
    il, iN = ndi.label(inner)
    if iN:
        big = il == (np.argmax(ndi.sum(inner, il, range(1, iN + 1))) + 1)
        iys, ixs = np.nonzero(big)
        print(
            f"  buckle interior: {(ixs.max() - ixs.min() + 1) / R:.3f} by {(iys.max() - iys.min() + 1) / R:.3f}"
            f", {hexc(big, 1)}"
        )
    print(f"  buckle frame {hexc(keep & ~inner, 1)}")

# --- colours ----------------------------------------------------------------
print("\ncolours")
print(f"  coat     {hexc(coat)}")
print(f"  dress    {hexc(dress)}")
print(f"  belt     {hexc(belt & pale)}")

