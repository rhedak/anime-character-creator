"""Trace Mio's blazer (`docs/mio-plan.md`, M7).

`segments/school-blazer.png` is a true crop and the whole blazer, sleeves
included, but her hair lies over it in two places and the shirt under it in a
third, so three things are inferred and the rest is read straight off the pixels:

- **Her two side locks** hide the shoulders and the top of each sleeve (the white
  strips beside the torso). The blazer is one cloth across there, so the strips are
  filled: the shoulder runs on in a straight line from where it is last seen to the
  sleeve's tip, and the gap between sleeve and torso is closed down to the armpit.
- **The neck opening** has no clean edge in the segment, since the shirt layer cut it.
  Its edge is read off the composite instead: the bright region between the lapels
  (collar wings, throat, shirt front, ribbon) grown to the stroke's centre line.
- **The collar wings** hide the opening's top, so its walls run straight up from
  where the lapel edge is last seen.

Everything is one silhouette, the garment with its sleeves, because the reference
draws it as one fill. The line work inside it is traced as strokes: the two lapels'
outer edges (with their notches), the front line from the lapels' meeting point
down to the hem, the two side lines where the torso passes in front of the sleeve,
and the two pocket flaps. The buttons and the pocket flap are measured here and
emitted as small parts of their own (`emit_blazer.py`).

Cut coordinates are head radii on `tall_slender`, x from the blazer's own centre line
(`AXIS_X`, the silhouette's middle), y from the head centre.

    ./harness/run.sh harness/mio/trace_blazer.py
"""

import json
import sys

import numpy as np
from common import CY, R, RGB, median_colour, segment
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as T  # noqa: E402

AXIS_X = 632.5
HALF = 2  # half the stroke with its antialiased edge, as the skirt's
TOL_SILHOUETTE = 0.016
TOL_LINE = 0.010

m, rgb = segment("school-blazer.png")
lum = rgb.sum(2)
ys, xs = np.nonzero(m)
print(f"blazer rows {ys.min()} to {ys.max()}, x {xs.min()} to {xs.max()}")


def runs(y):
    r = np.nonzero(m[y])[0]
    out, s, p = [], r[0], r[0]
    for x in r[1:]:
        if x != p + 1:
            out.append((int(s), int(p)))
            s = x
        p = x
    out.append((int(s), int(p)))
    return out


# --- the hair-hidden shoulders ------------------------------------------------------
# Where the torso's shoulder line stops being seen, and the sleeve's tip, each side.
LEFT_CORNER, LEFT_TIP = (535, 448), (502, 464)
RIGHT_CORNER, RIGHT_TIP = (725, 450), (765, 464)
ARMPIT_ROW = 700  # sleeve and torso are one run well before this (the gap fill loop's bound)
ARMPIT = 646  # the row where the side line begins

fill = m.copy()
for y in range(448, ARMPIT_ROW):
    rr = runs(y)
    if y >= LEFT_TIP[1] and len(rr) < 4:
        break  # the sleeves have met the torso: the armpit
    left_torso = next(r for r in rr if r[0] >= 530)
    right_torso = [r for r in rr if r[1] <= 735][-1]
    left_sleeve = [r for r in rr if r[1] <= 520]
    right_sleeve = [r for r in rr if r[0] >= 745]
    if left_sleeve:
        fill[y, left_sleeve[0][1] + 1 : left_torso[0]] = True
    elif y >= LEFT_CORNER[1]:
        t = (y - LEFT_CORNER[1]) / (LEFT_TIP[1] - LEFT_CORNER[1])
        x0 = int(round(LEFT_CORNER[0] + t * (LEFT_TIP[0] - LEFT_CORNER[0])))
        fill[y, x0 : left_torso[0]] = True
    if right_sleeve:
        fill[y, right_torso[1] + 1 : right_sleeve[0][0]] = True
    elif y >= RIGHT_CORNER[1]:
        t = (y - RIGHT_CORNER[1]) / (RIGHT_TIP[1] - RIGHT_CORNER[1])
        x1 = int(round(RIGHT_CORNER[0] + t * (RIGHT_TIP[0] - RIGHT_CORNER[0])))
        fill[y, right_torso[1] + 1 : x1 + 1] = True
# --- the neck opening, from the composite ---------------------------------------------
BOX = (586, 418, 680, 612)  # x0, y0, x1, y1 around the throat and the lapels' V
bx0, by0, bx1, by1 = BOX
# Per row, walk in from each side over the lapel (navy or ink) and stop at the first
# bright pixel: that is the opening's wall, at the white edge of the stroke. A row
# where the walk meets nothing bright is below the V's tip.
dark = RGB.sum(2) <= 170
# The ribbon's own black outline is dark too and, where it lies against a lapel with no
# white between, the walk would carry on through it: the ribbon is never the lapel.
ribbon, _ = segment("blue-ribbon.png")
dark &= ~ndi.binary_dilation(ribbon, iterations=2)
opening = np.zeros_like(fill)
for y in range(by0, by1):
    row = dark[y]
    left = bx0
    while left < bx1 and row[left]:
        left += 1
    right = bx1 - 1
    while right > bx0 and row[right]:
        right -= 1
    if left < right:
        opening[y, left : right + 1] = True
opening = ndi.binary_opening(opening, iterations=1)
# The lapels' inner edge has no ink line in the segment: it is the shirt layer's own cut,
# and ragged. Below the collar wings (rows 462 on) each wall is smoothed to a plain slope,
# which is what the cloth's edge is; above, it is the wings' straight outer edge.
SMOOTH_FROM, WIN = 462, 41
rows = np.arange(by0, int(np.nonzero(opening)[0].max()) + 1)
lo = np.array([np.nonzero(opening[y])[0].min() for y in rows], float)
hi = np.array([np.nonzero(opening[y])[0].max() for y in rows], float)
k = WIN // 2


def smooth(v):
    pad = np.pad(v, k, mode="edge")
    return np.convolve(pad, np.ones(WIN) / WIN, mode="valid")


sel = rows >= SMOOTH_FROM
lo_s, hi_s = lo.copy(), hi.copy()
# Smoothing a V's two walls pulls its tip open; keep the last rows to their own edges,
# so the tip stays a point.
lo_s[sel] = smooth(lo[sel])
hi_s[sel] = smooth(hi[sel])
opening = np.zeros_like(opening)
for y, a, b in zip(rows, lo_s, hi_s):
    opening[y, int(round(a)) : int(round(b)) + 1] = True
oy, ox = np.nonzero(opening)
print(f"opening rows {oy.min()} to {oy.max()}, x {ox.min()} to {ox.max()}")

base = fill.copy()
# The chest between the segment's ragged neck edge and the true opening: solid.
base[418:612, 588:678] = True
sil = ndi.binary_erosion(base, iterations=HALF) & ~ndi.binary_dilation(opening, iterations=HALF)
# Drop crumbs the subtraction leaves (the opening's walls are the real edge).
lab, n = ndi.label(sil, structure=np.ones((3, 3)))
sizes = ndi.sum(sil, lab, range(1, n + 1))
sil = lab == (1 + int(np.argmax(sizes)))
sy, sx = np.nonzero(sil)
print(f"silhouette x {sx.min()} to {sx.max()}, rows {sy.min()} to {sy.max()}, centre {(sx.min() + sx.max()) / 2:.1f}")


def to_cut(pt):
    return ((pt[0] - AXIS_X) / R, (pt[1] - CY) / R)


pts = [to_cut(p) for p in T.boundary(sil)]
silhouette = T.fit_closed(pts, TOL_SILHOUETTE)
print(f"silhouette: {len(silhouette[1])} segments, colour {median_colour(m, rgb, 6)}")

# --- the line work ---------------------------------------------------------------------
# Buttons first, so their ink rings are not mistaken for a line.
gold = m & (np.abs(rgb - np.array([189, 153, 87])).sum(2) < 90)
glab, gn = ndi.label(gold)
buttons = []
for i in range(1, gn + 1):
    c = glab == i
    if c.sum() < 40:
        continue
    by, bx = np.nonzero(c)
    buttons.append({"x": float(bx.mean()), "y": float(by.mean()), "r": float(np.sqrt(c.sum() / np.pi))})
buttons.sort(key=lambda b: b["y"])
print("buttons:", [(round(b["x"], 1), round(b["y"], 1), round(b["r"], 1)) for b in buttons])
near_button = ndi.binary_dilation(gold, iterations=7)

# The ink lines cut the garment into regions: the two lapel facings, the torso's two
# fronts, the two lower sleeves (the torso's side line parts them from the torso) and the
# two pocket flaps. Each region grown by half the stroke has its boundary on the stroke's
# centre line, which is the trace, with no thinning or junction splitting to go wrong.
ink = m & (lum <= 45)
inside = sil & ~ink
# Above the armpit the gap fill makes sleeve and torso one cloth, and only below it does a
# side line part them: a barrier across each sleeve at the armpit stands in for the seam
# that is hidden there, for the labelling alone.
barrier = inside.copy()
barrier[ARMPIT - 2 : ARMPIT, 440:540] = False
barrier[ARMPIT - 2 : ARMPIT, 726:825] = False
lab, n = ndi.label(barrier)
SEEDS = {
    "lapel_l": (585, 480),
    "lapel_r": (680, 480),
    "front_l": (580, 700),
    "front_r": (690, 700),
    "sleeve_l": (470, 700),
    "sleeve_r": (795, 700),
    "pocket_l": (532, 742),
    "pocket_r": (730, 742),
}
region = {}
for name, (x, y) in SEEDS.items():
    k = lab[y, x]
    assert k > 0, f"seed {name} is on ink"
    region[name] = lab == k
    ry, rx = np.nonzero(region[name])
    print(f"  {name}: {int(region[name].sum())} px, x {rx.min()}..{rx.max()}, y {ry.min()}..{ry.max()}")
assert len({int(lab[y, x]) for x, y in SEEDS.values()}) == len(SEEDS), "two seeds share a region"


def closed_chain(mask, clip=None, tol=TOL_LINE):
    grown = ndi.binary_dilation(mask, iterations=HALF)
    if clip is not None:
        grown &= clip
    return T.fit_closed([to_cut(p) for p in T.boundary(grown)], tol)


lapels = [closed_chain(region["lapel_l"], clip=ndi.binary_dilation(sil, iterations=1)), closed_chain(region["lapel_r"], clip=ndi.binary_dilation(sil, iterations=1))]
pocket = closed_chain(region["pocket_r"], tol=0.006)
print("lapels:", [len(c[1]) for c in lapels], "segments; pocket:", len(pocket[1]), "segments")


def open_chain(pts_px, extend_to=None, tol=TOL_LINE):
    """A fitted open chain through `pts_px`, its ends carried on along their own tangent
    to the rows in `extend_to` (so a line meets the outline it ends on)."""
    p = np.asarray(pts_px, float)
    k = 7
    sm = np.stack([np.convolve(np.pad(p[:, c], k // 2, mode="edge"), np.ones(k) / k, mode="valid") for c in (0, 1)], 1)
    if extend_to is not None:
        top, bottom = extend_to
        t0 = sm[0] - sm[min(8, len(sm) - 1)]
        t0 /= np.hypot(*t0)
        up = [sm[0] + t0 * s for s in range(1, int((sm[0][1] - top) / max(abs(t0[1]), 1e-6)) + 1)][::-1]
        t1 = sm[-1] - sm[max(-9, -len(sm))]
        t1 /= np.hypot(*t1)
        dn = [sm[-1] + t1 * s for s in range(1, int((bottom - sm[-1][1]) / max(abs(t1[1]), 1e-6)) + 1)]
        sm = np.array([*up, *sm, *dn])
    cut_pts = [to_cut(q) for q in sm]
    return T.fit_chain(cut_pts, T.simplify(cut_pts, tol))


# The front line: the middle of the gap between the two fronts, from below the lapels'
# V to the hem's notch.
rows = list(range(612, 858))
mid = []
for y in rows:
    a = np.nonzero(region["front_l"][y])[0].max()
    b = np.nonzero(region["front_r"][y])[0].min()
    mid.append(((a + b) / 2, y))
closure = open_chain(mid, extend_to=(597, 852))
# The side lines, where the torso passes in front of the sleeve: the sleeve region's inner
# edge, half a stroke in.
side_l, side_r = [], []
for y in range(650, 858):
    side_l.append((np.nonzero(region["sleeve_l"][y])[0].max() + HALF, y))
    side_r.append((np.nonzero(region["sleeve_r"][y])[0].min() - HALF, y))
side_l = open_chain(side_l, extend_to=(644, 856))
side_r = open_chain(side_r, extend_to=(644, 856))
print("lines:", len(closure[1]), len(side_l[1]), len(side_r[1]), "segments")

# The buttons and the pocket flap in the cut frame, for `emit_blazer.py`.
button_cut = [{"x": (b["x"] - AXIS_X) / R, "y": (b["y"] - CY) / R, "r": b["r"] / R} for b in buttons]
print("buttons in the cut frame:", [(round(b["x"], 3), round(b["y"], 3), round(b["r"], 3)) for b in button_cut])

json.dump(
    {
        "axis_x": AXIS_X,
        "silhouette": silhouette,
        "lapels": lapels,
        "lines": [closure, side_l, side_r],
        "pocket": pocket,
        "buttons": button_cut,
        "colour": median_colour(m, rgb, 6),
    },
    open("out/mio/blazer_trace.json", "w"),
)
print("wrote out/mio/blazer_trace.json")

# --- back over the reference, 2x --------------------------------------------------------
box = (435, 405, 830, 880)
S = 2
base_img = Image.fromarray(np.where(m[..., None], rgb, 255).astype("uint8")).crop(box)
comp = Image.fromarray(RGB.clip(0, 255).astype("uint8")).crop(box)
img = comp.resize((comp.width * S, comp.height * S), Image.LANCZOS)
d = ImageDraw.Draw(img)


def draw(c, colour, closed=True):
    q = T.sample_chain(c[0], c[1], 14)
    px = [((AXIS_X + x * R - box[0]) * S, (CY + y * R - box[1]) * S) for x, y in q]
    d.line(px + ([px[0]] if closed else []), fill=colour, width=2)


draw(silhouette, (255, 0, 80))
for c in lapels:
    draw(c, (0, 200, 255))
for c in (closure, side_l, side_r):
    draw(c, (255, 200, 0), closed=False)
draw(pocket, (0, 255, 120))
draw(closed_chain(region['pocket_l'], tol=0.006), (0, 255, 120))
img.save("out/mio/blazer_trace.png")
print("wrote out/mio/blazer_trace.png")
