"""Mio's hair, traced (`docs/mio-plan.md`, M8), off `segments/long-black-hair.png` and
`segments/bangs.png`, which together are the whole hair in front of her and beside her.

What it writes to `out/mio/hair_trace.json` and draws on `out/mio/hair_trace.png`:

- **The front piece**: both layers as one U-shaped silhouette, the face opening and the
  two curtains of the long locks, as one closed chain. Its outline is the stroke's centre
  line: on the opening and the lock edges the reference's ink lies inside the mask, and on
  the outer silhouette it lies just outside it, so the outer ink is added before the whole
  is eroded by half the stroke.
- **The mass behind**: the same silhouette closed straight across between the two curtains
  where the blazer hides it, down to `CLOSE_Y`.
- **The strands**: the ink inside the hair, thinned and split at its junctions, each long
  stroke one open chain.
- **The openings**: the holes in the hair's mask, ringed by ink, where skin shows through:
  an ear at each side and a small gap in the fringe.

    ./harness/run.sh harness/mio/trace_hair.py
"""

import json

import numpy as np
from common import CX, CY, R, RGB, prune, segment, strokes_of, thin
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import sys

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as T  # noqa: E402

HALF = 2
CONTOUR_SIGMA = 2.5  # pixels along the contour
CLOSE_Y = 700  # where the mass is closed across between the curtains, behind the blazer
SMOOTH = 1.5
HAT, HAT_MIN = 7, 12
FLAP_ROWS = (395, 450)  # rows of the streaked flaps, where no strand is taken
FLAP_TOP, FLAP_BOTTOM = 347, 446
FLAP_EDGE = (522.0, 0.111)  # the curtain's inner edge at FLAP_TOP, and its slope
EDGE_NEAR = 6
FRINGE_BOTTOM, MIN_LONG = 345, 30
MAX_THICK = 4.5
MIN_STROKE = 14
INK = 55  # luminance sum: her lines are black (0 to 30) and their edges
SHADE_MIN, SHADE_MAX = 55, 100  # the darker hair behind: (21, 22, 24) against (39, 40, 44)
MIN_SHADE_PX = 400
TOL_SHADE = 0.02
TOL_FRONT = 0.014
TOL_MASS = 0.016

lm, lrgb = segment("long-black-hair.png")
bm, brgb = segment("bangs.png")
F = lm | bm
# The composite, not the layers: the layers are flat fills without her line work, which
# only the composite has.
lum = RGB.sum(2)
ys, xs = np.nonzero(F)
print(f"front piece: rows {ys.min()} to {ys.max()}, x {xs.min()} to {xs.max()}, {F.sum()} px")


def to_frame(pt):
    return ((pt[0] - CX) / R, (pt[1] - CY) / R)


def smooth_loop(points, sigma=CONTOUR_SIGMA):
    """A closed contour with its pixel staircase rounded off: the coordinates averaged
    along the arc. Her edges are long smooth curves and the mask's boundary is not."""
    xy = np.asarray(points, float)
    return list(
        zip(
            ndi.gaussian_filter1d(xy[:, 0], sigma, mode="wrap"),
            ndi.gaussian_filter1d(xy[:, 1], sigma, mode="wrap"),
        )
    )


def silhouette(mask):
    """`mask` with its outer ink added, rounded and eroded to the stroke's centre line."""
    # The outer silhouette's ink lies outside the segment's mask: add the dark ring there.
    span = np.zeros_like(mask)
    for y in range(mask.shape[0]):
        row = np.nonzero(mask[y])[0]
        if len(row):
            span[y, row.min() : row.max() + 1] = True
    ring = ndi.binary_dilation(mask, iterations=4) & ~mask & (RGB.sum(2) <= 60) & ~span
    # The masks' own edges are a pixel ragged (the ring most of all): round them off.
    h = ndi.gaussian_filter((mask | ring).astype(float), SMOOTH) > 0.5
    er = ndi.binary_erosion(h, iterations=HALF)
    lab, n = ndi.label(er)
    return lab == (1 + int(np.argmax(ndi.sum(er, lab, range(1, n + 1)))))


# The flaps beside the neck are hair behind her, not hair in front: a lobe hanging from
# each curtain's inner edge, down to the blazer's shoulder, where the reference's blazer
# outline is the one line between them. They belong to the mass, behind the blazer, in the
# darker tone. The curtain's inner edge runs straight on past where they hang.
def flap_edge(y):
    """x of the left curtain's inner edge, from the lobe's top to the shoulder."""
    return FLAP_EDGE[0] + (min(max(y, FLAP_TOP), FLAP_BOTTOM) - FLAP_TOP) * FLAP_EDGE[1]


Her_full = silhouette(F)
cut = np.zeros_like(F)
for y in range(FLAP_TOP, FLAP_BOTTOM + 1):
    xl = int(round(flap_edge(y)))
    cut[y, xl + 1 : int(round(2 * CX)) - xl] = True
F_full = F
F = F & ~cut
Her = silhouette(F)

pts = [to_frame(p) for p in smooth_loop(T.boundary(Her))]
front = T.fit_closed(pts, TOL_FRONT)
print(f"front outline: {len(front[1])} segments")

# The mass: the silhouette with the gap between the two curtains filled, from the left
# curtain's inner edge to the right's, down to CLOSE_Y. Not the whole row's span: the
# daylight between a curtain's outer lock and its inner one has to stay open.
M = Her_full.copy()
mid = int(round(CX))
for y in range(F.shape[0]):
    left = np.nonzero(Her_full[y, :mid])[0]
    right = np.nonzero(Her_full[y, mid:])[0]
    if len(left) and len(right) and y <= CLOSE_Y:
        M[y, left.max() : mid + right.min() + 1] = True
mass = T.fit_closed([to_frame(p) for p in smooth_loop(T.boundary(M))], TOL_MASS)
print(f"mass outline: {len(mass[1])} segments")

# The darker hair behind the neck: the mass between the curtains below the flaps' top,
# a polygon running a little under each curtain (which covers it) and closed far below.
UNDER_TUCK = 6
UNDER_TOP = 290  # up beside the ear; the head covers what is not hair
poly = []
for y in (UNDER_TOP, FLAP_BOTTOM, CLOSE_Y):
    poly.append((flap_edge(y) - UNDER_TUCK, y))
for y in (CLOSE_Y, FLAP_BOTTOM, UNDER_TOP):
    poly.append((2 * CX - flap_edge(y) + UNDER_TUCK, y))
under_pts = [to_frame(q) for q in poly]
underside = (
    under_pts[0],
    [(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b) for a, b in zip(under_pts, under_pts[1:] + under_pts[:1])],
)

json.dump({"front": front, "mass": mass, "underside": underside}, open("out/mio/hair_trace.json", "w"))

# A picture: the reference with the front outline in red and the mass in blue.
im = Image.fromarray(RGB.astype(np.uint8)).convert("RGB")
d = ImageDraw.Draw(im)


def px(p):
    return (CX + p[0] * R, CY + p[1] * R)


for chain, colour in ((mass, (40, 80, 230)), (front, (220, 30, 30))):
    pts = [px(p) for p in T.sample_chain(*chain)]
    d.line(pts, fill=colour, width=1)
im.crop((400, 40, 870, 770)).resize((940, 1460), Image.LANCZOS).save("out/mio/hair_trace.png")
print("wrote out/mio/hair_trace.json, hair_trace.png")

# --- the ears --------------------------------------------------------------------------
# What shows of each ear is a thin sliver of skin: a hole in the hair's mask, ringed by ink
# that lies inside the mask, so the hole grown by half the stroke is the ring's centre line.
holes = ndi.binary_fill_holes(F) & ~F
hlab, hn = ndi.label(holes)
ears, ear_zone = [], np.zeros_like(F)
for i in range(1, hn + 1):
    c = hlab == i
    ey, ex = np.nonzero(c)
    if c.sum() < 100 or ey.mean() < 250:
        # (a small gap in her fringe, up at the brow, is skin showing between two locks: it
        # reads as a scratch under our heavier stroke, so it is left out)
        continue
    grown = ndi.binary_dilation(c, iterations=HALF)
    chain = T.fit_closed([to_frame(p) for p in T.boundary(grown)], 0.008)
    print(f"opening at ({ex.mean():.0f}, {ey.mean():.0f}), {c.sum()} px, {len(chain[1])} segments")
    ears.append(chain)
    ear_zone |= ndi.binary_dilation(c, iterations=7)
ears.sort(key=lambda ch: ch[0][0])

# --- the strands -----------------------------------------------------------------------
# Ink inside the hair, away from its own outline (which the front chain already is) and
# from the ears' rings.
inner = ndi.binary_erosion(F, iterations=4)
# A line is a thin dark structure against what lies round it, whichever tone that is: a
# black-hat (the closing less the image) picks out dark runs narrower than the window, and
# leaves the wide darker regions alone.
blackhat = ndi.grey_closing(lum.astype(float), size=(HAT, HAT)) - lum
# The flaps beside the neck are streaked with ink, a texture and not lines.
flaps = np.zeros_like(F)
flaps[FLAP_ROWS[0] : FLAP_ROWS[1], 515:745] = True
ear_zone = ear_zone | flaps
strong = inner & (lum <= INK) & ~ear_zone
# Her thin lines are grey along their length and black only in places, so a threshold
# breaks each into fragments: keep everything line-like that touches a strong pixel.
weak = inner & ((lum <= INK) | (blackhat >= HAT_MIN)) & ~ear_zone
wl, wn = ndi.label(weak, structure=np.ones((3, 3)))
has_strong = np.zeros(wn + 1, bool)
has_strong[np.unique(wl[strong])] = True
ink = has_strong[wl] & (wl > 0)
lab2, n2 = ndi.label(ink, structure=np.ones((3, 3)))
strokes = np.zeros_like(ink)
for i in range(1, n2 + 1):
    c = lab2 == i
    if c.sum() < 12:
        continue
    # A blotch is not a line: the flaps beside the neck carry streaks of ink, thick and
    # webbed, which would thin to a net of short strokes. A line is a few pixels across.
    thickness = c.sum() / max(1, thin(c).sum())
    if thickness > MAX_THICK:
        continue
    strokes |= c
print(f"stroke ink {strokes.sum()} px")
skel = thin(strokes)
paths = strokes_of(prune(skel), min_len=MIN_STROKE)
print(f"{len(paths)} strokes, lengths", sorted(len(p) for p in paths)[::-1][:30])

TOL_STRAND = 0.012
outside = ndi.distance_transform_edt(F)  # distance to the nearest pixel outside the hair


def extend(path):
    """Run each end of a stroke on to the hair's edge when it stops just short of it."""
    pts = [(float(x), float(y)) for x, y in path]
    for end in (0, -1):
        k = 8
        a = np.array(pts[end])
        b = np.array(pts[end + k] if end == 0 else pts[end - k]) if len(pts) > k else np.array(pts[-1 - end])
        d = a - b
        norm = np.hypot(*d)
        if norm == 0:
            continue
        d /= norm
        for step in range(1, 12):
            q = a + d * step
            yy, xx = int(round(q[1])), int(round(q[0]))
            if not (0 <= yy < F.shape[0] and 0 <= xx < F.shape[1]) or not F[yy, xx]:
                break
        else:
            continue
        if step <= 11:
            tip = a + d * (step - 1)
            pts.insert(0, tuple(tip)) if end == 0 else pts.append(tuple(tip))
    return pts


edge_dist = ndi.distance_transform_edt(Her)  # from each pixel to the front's outline
strands = []
for path in paths:
    px_, py_ = [q[0] for q in path], [q[1] for q in path]
    # Below the fringe a short fragment is a dash, where above it a short line is a lock's
    # edge: her long lines there come out whole, so a short one is a piece of something.
    if np.mean(py_) > FRINGE_BOTTOM and len(path) < MIN_LONG:
        continue
    # The near-horizontal marks at the fringe's foot are her eyebrows showing through it,
    # which are the face's, not the hair's.
    if (max(px_) - min(px_)) > 1.2 * (max(py_) - min(py_)):
        continue
    # A stroke lying along the outline is the outline again: half of it would be clipped away.
    on_edge = np.mean([edge_dist[int(y), int(x)] < EDGE_NEAR for x, y in path])
    if on_edge > 0.5:
        continue
    pts = extend(path)
    if len(pts) < 3:
        continue
    fr = [to_frame(p) for p in pts]
    marks = T.simplify(fr, TOL_STRAND)
    strands.append(T.fit_chain(fr, marks))
# Top to bottom, left to right, so the emitted order is stable.
strands.sort(key=lambda ch: (round(ch[0][0] * 4), ch[0][1]))
print(f"{len(strands)} strands, {sum(len(c[1]) for c in strands)} segments")

# --- the darker hair behind -------------------------------------------------------------
# Hers has two tones of black: the main fill (39, 40, 44) and a darker one (21, 22, 24) in
# strips down the outer side of each curtain, in the flaps beside the neck and in a few
# patches at the temple, where the hair behind shows. The antialiased edge of every ink line
# passes through the darker tone's range, so a thin opening takes that halo off first.
# The flaps beside the neck are darker with streaks of ink through them, so ink counts as
# the darker hair here and the opening, which takes thin things off, removes the lines.
darker = F & (lum <= SHADE_MAX)
darker = ndi.binary_opening(darker, structure=np.ones((3, 3)), iterations=3)
darker = ndi.binary_closing(darker, structure=np.ones((3, 3)), iterations=3)
darker = ndi.gaussian_filter(ndi.binary_fill_holes(darker).astype(float), 2.5) > 0.5
darker &= ~ear_zone
slab, sn = ndi.label(darker)
shade = []
for i in range(1, sn + 1):
    c = slab == i
    if c.sum() < MIN_SHADE_PX:
        continue
    grown = ndi.binary_dilation(c, iterations=HALF)
    ch = T.fit_closed([to_frame(p) for p in T.boundary(grown)], TOL_SHADE)
    sy, sx = np.nonzero(c)
    print(f"darker region at ({sx.mean():.0f}, {sy.mean():.0f}), {c.sum()} px, {len(ch[1])} segments")
    shade.append(ch)
shade.sort(key=lambda ch: (ch[0][1] > 0.9, ch[0][0]))

data = json.load(open("out/mio/hair_trace.json"))
data.update({"openings": ears, "strands": strands, "shade": shade})
json.dump(data, open("out/mio/hair_trace.json", "w"))
for chain in strands:
    d.line([px(p) for p in T.sample_chain(*chain)], fill=(0, 170, 60), width=1)
for chain in ears:
    d.line([px(p) for p in T.sample_chain(*chain)], fill=(230, 120, 0), width=1)
for chain in shade:
    d.line([px(p) for p in T.sample_chain(*chain)], fill=(200, 0, 200), width=1)
im.crop((400, 40, 870, 770)).resize((940, 1460), Image.LANCZOS).save("out/mio/hair_trace.png")

# A second picture on the stretched-contrast reference, where her lines can be seen:
# every strand in red, the darker regions in magenta, the openings in orange.
stretch = np.clip(RGB.sum(2) / 140 * 255, 0, 255).astype(np.uint8)
im2 = Image.fromarray(stretch).convert("RGB")
d2 = ImageDraw.Draw(im2)
for chain in strands:
    d2.line([px(p) for p in T.sample_chain(*chain)], fill=(255, 0, 0), width=1)
for chain in shade:
    d2.line([px(p) for p in T.sample_chain(*chain)], fill=(200, 0, 200), width=1)
for chain in ears:
    d2.line([px(p) for p in T.sample_chain(*chain)], fill=(255, 140, 0), width=1)
im2.crop((400, 40, 870, 770)).resize((940, 1460), Image.NEAREST).save("out/mio/hair_trace_contrast.png")

dbg = np.full((*F.shape, 3), 255, np.uint8)
dbg[F] = (225, 225, 225)
dbg[ink] = (0, 0, 0)
dbg[skel] = (255, 0, 0)
Image.fromarray(dbg[40:770, 400:870]).resize((940, 1460), Image.NEAREST).save("out/mio/hair_dbg.png")
