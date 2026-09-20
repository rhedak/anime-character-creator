"""Trace Satoshi's katana off `ref-local/satoshi-tall-chibi-katana/`, in head radii.

Method: `.claude/skills/trace-reference/SKILL.md`. The segment export
`segments/katana.png` is an exact crop of the composite (`locate` in the notes:
mean RGB difference 0.58 at offset (673, 584), the same for `sword-hilt.png` and
`sword-scabbard.png`), unlike the grok layer exports, so its alpha and its fill
components are used directly. Only the silhouettes and flat colours transfer.

Calibration is the one `harness/body/satoshi_tall_chibi_landmarks.py` derived
for this figure (the same generator's figure, head centre (626, 308) and about
172 px per head radius; the widest row of face skin on this composite gives
625.6, 307.8 and 170.5).

The katana is a rigid prop, so its chains are in a **sword-local frame**, not the
figure's: origin at the tsuba's centre, `u` along the sword's own axis toward the
tip, `v` across it (`n = (-a_y, a_x)`, the convention `_staff_placement` uses),
both in the reference's head radii. `_katana_placement` puts that frame on our
figure at its own angle, position and scale.

Shapes, in drawing order:
  saya       the scabbard's whole silhouette, koiguchi ring to kojiri
  ring_dark  the dark ring under the guard
  ring_brown the wide brown band under it
  kojiri     the end cap
  tsuba      the guard
  fuchi      the collar the handle comes out of
  tsuka      the handle's silhouette
  diamonds   the cream rayskin diamonds showing through the wrap
  kashira    the pommel cap
"""

import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, "/Users/henrik/git/anime-character-creator/.claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

BASE = "ref-local/satoshi-tall-chibi-katana"
OUT = "out/katana"
OFF = (673, 584)  # where segments/katana.png sits in the composite
OX, OY, R = 626.0, 308.0, 171.5
HALF = 2  # half the reference's outline width, in pixels

k = np.asarray(Image.open(f"{BASE}/segments/katana.png").convert("RGBA")).astype(int)
alpha = k[..., 3] > 128
rgb = k[..., :3]
s = rgb.sum(2)
disk = ndi.generate_binary_structure(2, 1)


def grow(m, n):
    return ndi.binary_dilation(m, structure=disk, iterations=n) if n else m


def close(m, n):
    return ndi.binary_fill_holes(ndi.binary_erosion(grow(m, n), structure=disk, iterations=n))


def hexc(m):
    inner = ndi.binary_erosion(m, structure=disk, iterations=2)
    px = rgb[inner if inner.any() else m]
    return "#%02x%02x%02x" % tuple(int(v) for v in np.median(px, axis=0))


lab, _ = ndi.label((s > 60) & alpha)


def comp(i, bbox):
    m = lab == i
    ys, xs = np.nonzero(m)
    got = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    assert all(abs(a - b) <= 2 for a, b in zip(got, bbox)), (i, got, bbox)
    return m


kashira = comp(1, (4, 5, 44, 35))
fuchi = comp(24, (45, 188, 85, 220))
tsuba = comp(27, (24, 199, 109, 238))
ring_dark = comp(32, (51, 230, 94, 260))
ring_brown = comp(35, (53, 248, 102, 285))
saya_body = comp(37, (63, 277, 169, 599))
kojiri = comp(102, (136, 590, 175, 629))

# The handle: every dark wrap piece above the collar. The diamonds are cream, and
# separate fills of their own; the handle silhouette takes them in too.
taken = kashira | fuchi | tsuba | ring_dark | ring_brown | saya_body | kojiri
wrap = np.zeros(s.shape, bool)
for i, sl in enumerate(ndi.find_objects(lab), start=1):
    if sl is None:
        continue
    m = lab[sl] == i
    ys, xs = sl
    if m.sum() < 25 or ys.start > 205 or (m & taken[sl]).any():
        continue
    # The crop keeps a sliver of the tunic's green beside the handle (component
    # 10, 62 px): the wrap is neutral dark, so anything greener than it is not.
    r_, g_, b_ = np.median(rgb[sl][m], axis=0)
    if g_ - r_ > 4:
        continue
    wrap[sl] |= m
cream = (s > 380) & alpha & (np.arange(s.shape[0])[:, None] < 205)
cream = ndi.binary_opening(cream, iterations=1)
dlab, dn = ndi.label(cream)
diamonds = [dlab == i for i in range(1, dn + 1) if (dlab == i).sum() >= 60]
diamonds.sort(key=lambda m: np.nonzero(m)[0].mean())
print("diamonds", len(diamonds), [int(m.sum()) for m in diamonds])
# --- the sword's own axis: the scabbard's principal direction, pointing to the tip
ys, xs = np.nonzero(saya_body)
c = np.array([xs.mean(), ys.mean()])
_, _, vt = np.linalg.svd(np.stack([xs - c[0], ys - c[1]], 1), full_matrices=False)
a = vt[0] if vt[0][1] > 0 else -vt[0]
a = a / np.linalg.norm(a)
theta = math.degrees(math.atan2(a[0], a[1]))
n = np.array([-a[1], a[0]])
ty, tx = np.nonzero(tsuba)
origin = np.array([tx.mean(), ty.mean()])
print("axis", a, "tilt from vertical %.2f deg" % theta, "tsuba centre (crop px)", origin)

# The wrap meets the collar along a **straight line across the sword's axis**. The
# reference's collar rises to a peak in the middle of that join, which reads as a
# bent line at this size; the owner asked for it straight. So both shapes are cut
# along one line, perpendicular to the axis at the height of the collar's corners
# (its top edge over the outer quarter of its width each side, below the peak): the
# collar keeps what is below it, and the wrap takes the peak's pixels and runs down.
YY, XX = np.mgrid[0 : s.shape[0], 0 : s.shape[1]]
U = ((XX - origin[0]) * a[0] + (YY - origin[1]) * a[1]) / R
V = ((XX - origin[0]) * n[0] + (YY - origin[1]) * n[1]) / R
fu, fv = U[fuchi], V[fuchi]
across = (fv - fv.min()) / (fv.max() - fv.min())
U_LINE = float(np.mean([np.percentile(fu[across <= 0.25], 5), np.percentile(fu[across >= 0.75], 5)]))
print("collar top edge at the corners, u = %.3f (peak at %.3f)" % (U_LINE, fu.min()))
hump = fuchi & (U < U_LINE)
fuchi = fuchi & (U >= U_LINE)
tsuka = close(wrap | np.logical_or.reduce(diamonds) | hump, 4) & (U <= U_LINE) & ~grow(fuchi | kashira, 0)

saya = close(saya_body | ring_dark | ring_brown | kojiri, 3)



def local(pts):
    """Crop pixels -> sword-local head radii (u along the axis, v across)."""
    out = []
    for x, y in pts:
        d = (np.array([x, y], float) - origin) / R
        out.append((float(d @ a), float(d @ n)))
    return out


def trace(mask, tol):
    contour = tl.boundary(grow(mask, HALF))
    start, segs = tl.fit_closed(local(contour), tol)
    return {"start": start, "segs": segs}


shapes = {
    "saya": trace(saya, 0.010),
    "ring_dark": trace(ring_dark, 0.010),
    "ring_brown": trace(ring_brown, 0.010),
    "kojiri": trace(kojiri, 0.010),
    "tsuba": trace(tsuba, 0.010),
    "fuchi": trace(fuchi, 0.010),
    "tsuka": trace(tsuka, 0.010),
    "kashira": trace(kashira, 0.010),
}


def snap_to_line(chain, on_edge):
    """Put every point of `chain` that `on_edge` picks on the line u = U_LINE.

    The join is straight in the sword's frame, but a fit to its pixels is not: the
    line runs at 12.8 degrees to the pixel grid, so the boundary is a staircase and
    each fitted segment bulges a little either way, which read as a wobble. The
    wrap's bottom edge and the collar's top edge are both the line, exactly: snap
    every start, control and end point near it onto it, so the segments between
    them are straight. The points on the sides keep their fitted positions.
    """

    def snap(pt):
        return (U_LINE, pt[1]) if on_edge(pt) else pt

    return {
        "start": snap(chain["start"]),
        "segs": [(snap(c), snap(e)) for c, e in chain["segs"]],
    }


shapes["tsuka"] = snap_to_line(shapes["tsuka"], lambda pt: pt[0] > U_LINE - 0.04)
shapes["fuchi"] = snap_to_line(shapes["fuchi"], lambda pt: pt[0] < U_LINE + 0.02)
dia = [trace(m, 0.008) for m in diamonds]
colours = {
    "saya": hexc(saya_body),
    "ring_dark": hexc(ring_dark),
    "ring_brown": hexc(ring_brown),
    "kojiri": hexc(kojiri),
    "tsuba": hexc(tsuba),
    "fuchi": hexc(fuchi),
    "tsuka": hexc(wrap),
    "diamonds": hexc(np.logical_or.reduce(diamonds)),
    "kashira": hexc(kashira),
}
print("colours", colours)
for name, ch in shapes.items():
    print(f"{name:10s} {len(ch['segs']):3d} segments")
print("diamonds", [len(d["segs"]) for d in dia])

# --- landmarks, in the sword-local frame and in the reference's own head radii
allpts = np.array(
    [q for m in (saya, tsuka, kashira, tsuba) for q in local(tl.boundary(grow(m, HALF)))]
)
land = {
    "tip_u": float(allpts[:, 0].max()),
    "pommel_u": float(allpts[:, 0].min()),
    "width_v": [float(allpts[:, 1].min()), float(allpts[:, 1].max())],
    "tilt_deg": theta,
    "tsuba_ref": [(origin[0] + OFF[0] - OX) / R, (origin[1] + OFF[1] - OY) / R],
}
print("landmarks", land)
# The belt the sword hangs from, on the same composite: `segments/brown-belt.png` is
# a crop too (found by matching), so its alpha is the belt's own extent.
comp = np.asarray(Image.open(f"{BASE}/satoshi-tall-chibi-sword.png").convert("RGBA")).astype(int)
belt = np.asarray(Image.open(f"{BASE}/segments/brown-belt.png").convert("RGBA")).astype(int)
bh_, bw_ = belt.shape[:2]
bmask = belt[..., 3] > 200
best = None
for oy in range(725, 750):
    for ox in range(515, 535):
        diff = np.abs(comp[oy : oy + bh_, ox : ox + bw_, :3] - belt[..., :3]).sum(2)[bmask].mean()
        if best is None or diff < best[0]:
            best = (diff, ox, oy)
_, box, boy = best
bys, bxs = np.nonzero(belt[..., 3] > 128)
land["belt_ref"] = {
    "centre_y": float((bys.mean() + boy - OY) / R),
    "half_w": float((bxs.max() - bxs.min() + 1) / 2 / R),
    "centre_x": float(((bxs.max() + bxs.min()) / 2 + box - OX) / R),
    "match_diff": float(best[0]),
}
print("belt", land["belt_ref"])
json.dump(
    {"shapes": shapes, "diamonds": dia, "colours": colours, "landmarks": land},
    open(f"{OUT}/katana_trace.json", "w"),
)

# --- overlay: the fitted chains over the crop, enlarged, so an eye can check them
S = 3
img = Image.new("RGB", (k.shape[1] * S, k.shape[0] * S), (255, 255, 255))
base = Image.fromarray(np.where(alpha[..., None], rgb, 255).astype("uint8")).resize(img.size, Image.NEAREST)
img.paste(base)
d = ImageDraw.Draw(img)


def to_px(p):
    return (origin + p[0] * R * a + p[1] * R * n) * S


palette = ["#ff0000", "#00aa00", "#0000ff", "#ff00ff", "#00aaaa", "#ff8800", "#8800ff", "#888800", "#ff0088"]
for i, (name, ch) in enumerate(list(shapes.items()) + [("d", x) for x in dia]):
    pts = tl.sample_chain(ch["start"], ch["segs"], 10)
    d.line([tuple(to_px(p)) for p in pts], fill=palette[i % len(palette)], width=1)
img.save(f"{OUT}/overlay.png")
print("overlay", img.size)
