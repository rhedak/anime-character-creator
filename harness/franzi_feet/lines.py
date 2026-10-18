"""The foot's interior lines: the dividers between toes and the nails, traced from the close-up.

    ./harness/run.sh harness/franzi_feet/lines.py

Dividers. The toes touch, separated by a dark shadow line that starts at the base of the toes and widens toward the tips. For each pair of
neighbouring toes (foot A, viewer's left: toes 9, 6, 10, 7, 5, little to big) the segment layers (locate.py) give the two toes' masks, so the
line between them is the midline of the gap between their facing edges, row by row, over the rows where both exist (the shorter toe's tip
ends it, at the notch in the outline). The midline is snapped across the line to the darkest pixel of the close-up (the shadow itself), and
its thickness is measured along it (how far each pixel is from skin brightness toward shadow darkness, summed across the line), so a divider
is thin at its base and heavy at the notch, as in the reference. Widths are stored in head radii on ref 04.

Nails. Each toenail is a slightly lighter oval with a thin darker rim. From a centre guess (below) rays are cast and, along each, the
darkest point of the rim is taken within a radius window, then the ring is smoothed and fitted. Centres and sizes are read off the grid in
view.py. Writes out/franzi_feet/lines.json (chains in [v, d] body coordinates, see outline.py) and ts/src/body-adult-foot-lines-data.ts.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/franzi_feet")
H, CX, CHIN = 352.0, 668.2, 434.0
S_RAD = 175.7  # ref 04 px per head radius
F = json.load(open(OUT / "foot.json"))
s, dx, dy = F["s"], F["dx"], F["dy"]
L = np.load(OUT / "layers.npz")
img = np.array(Image.open("ref/franzi/hands/feet-front.png").convert("RGBA")).astype(float)
lum = img[..., :3].mean(2)
alpha = img[..., 3]
SKIN, DARK = 212.0, 60.0
W_MIN, W_MAX = 0.6, 4.2  # px on ref 04: a floor so a faint line still draws, a cap so an open gap's edge does not inflate it


def to_body(x, y):
    """Close-up px (foot A's frame) to [v, d] body coordinates."""
    return ((CX - (x * s + dx)) / H, ((y * s + dy) - CHIN) / H)


# --- dividers
ORDER = [9, 6, 10, 7, 5]
dividers, widths = [], []
for a, b in zip(ORDER, ORDER[1:]):
    ma, mb = L[f"toe_{a}"], L[f"toe_{b}"]
    rows = [r for r in range(ma.shape[0]) if ma[r].any() and mb[r].any()]
    r0, r1 = rows[0] + 12, rows[-1] - 6
    mid = []
    for r in range(r0, r1 + 1):
        xa = np.nonzero(ma[r])[0].max()
        xb = np.nonzero(mb[r])[0].min()
        mid.append((r, (xa + xb) / 2.0))
    # A divider ends where the page shows through between the toes (the close-up is transparent at the midline): below that there is no
    # shadow line, and the outline already follows the gap beside the big toe. (Judged by alpha: a first version used the mask gap width and
    # the brightness test read transparent pixels, which are black, as shadow.)
    # The outline is closed over narrow slits between toes (outline.py), so where the page shows between two toes the divider carries on down
    # the middle of that slit to the notch where the outline's two lobes meet (the row of the narrowest gap), drawn thin, instead of stopping
    # and leaving skin with no line in it. Up to there it snaps to the shadow line; in the slit there is no shadow to snap to.
    gaps = np.array([np.nonzero(mb[int(r)])[0].min() - np.nonzero(ma[int(r)])[0].max() for r, _ in mid])
    has_slit = (a, b) == (7, 5)  # only the pair with the open gap beside the big toe (the others touch down to their tips)
    stop = int(np.argmin(gaps[: max(1, len(gaps) - 4)])) + 3 if has_slit else len(mid)
    mid = np.array(mid[: min(stop, len(mid))], float)
    page = np.array([alpha[int(r), int(xm)] < 128 for r, xm in mid])
    xs = []
    for (r, xm), pg in zip(mid, page):
        if pg:
            xs.append(float(xm))
            continue
        lo, hi = int(xm) - 7, int(xm) + 8
        seg = ndimage.gaussian_filter1d(lum[int(r), lo:hi], 1.0)
        xs.append(lo + int(np.argmin(seg)))
    xs = ndimage.gaussian_filter1d(np.array(xs, float), 12.0 if has_slit else 6.0, mode="nearest")  # the slit pair joins a snapped stretch to an unsnapped one: smooth harder
    ys = mid[:, 0]
    # thickness across the line at each row, in close-up px, then to ref 04 px and head radii
    wcc = []
    for r, x in zip(ys, xs):
        cols = np.arange(int(x) - 14, int(x) + 15)
        row = lum[int(r), cols]
        cover = np.clip((SKIN - row) / (SKIN - DARK), 0, 1)
        wcc.append(cover.sum())
    w04 = ndimage.gaussian_filter1d(np.array(wcc) * s, 8.0, mode="nearest")
    w04 = np.clip(w04, W_MIN, W_MAX)
    w04[page] = np.minimum(w04[page], 2.0)  # a line down the slit between two toes is thin, whatever the gap's own width
    idx = np.linspace(0, len(ys) - 1, 9).astype(int)
    pts = [to_body(x, y) for x, y in zip(xs, ys)]
    start, segs = tl.fit_chain(pts, tl.simplify(pts, 0.0016))
    dividers.append([list(start), [[list(c), list(e)] for c, e in segs]])
    widths.append([float(w04[i] / S_RAD) for i in idx])
    print(f"divider {a}/{b}: rows {int(ys[0])}..{int(ys[-1])}, {len(segs)} segments, thickness {w04.min():.1f}..{w04.max():.1f} px (ref 04)")

# --- nails: (toe, centre x, centre y, half width, half height) in close-up px, read off the grid in view.py (foot A, little toe to big toe)
NAILS = [(9, 165, 1362, 12, 14), (6, 210, 1405, 15, 15), (10, 263, 1429, 18, 17), (7, 323, 1453, 21, 19), (5, 418, 1437, 38, 33)]
nails = []
sm = ndimage.gaussian_filter(lum, 0.8)
for toe, cx, cy, rx, ry in NAILS:
    # the big toe's rim runs beside the dark wedge between it and the next toe, which the search took for the rim: keep its search near the ring
    ts = np.linspace(0.9, 1.15, 40) if toe == 5 else np.linspace(0.78, 1.3, 60)
    ang = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    best = []
    for th in ang:
        xs_ = cx + ts * rx * np.cos(th)
        ys_ = cy + ts * ry * np.sin(th)
        v = ndimage.map_coordinates(sm, [ys_, xs_], order=1)
        # the rim is a thin dark line on lighter skin: darkest point, pulled toward the guessed ring so a toe's own shadow edge does not win
        best.append(ts[int(np.argmin(v + 28 * np.abs(ts - 1.0)))])
    best = ndimage.gaussian_filter1d(np.array(best), 3.0, mode="wrap")
    ring = [(cx + t * rx * np.cos(th), cy + t * ry * np.sin(th)) for t, th in zip(best, ang)]
    body = [to_body(x, y) for x, y in ring]
    nails.append(tl.fit_closed(body, 0.0016))
    print(f"nail on toe {toe}: ring scale {best.min():.2f}..{best.max():.2f}, {len(nails[-1][1])} segments")
json.dump({"dividers": dividers, "divider_widths": widths, "nails": [[list(a), [[list(c), list(e)] for c, e in b]] for a, b in nails]}, open(OUT / "lines.json", "w"))


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


def chain_ts(c):
    st, sg = c
    return f"[{pt(st)}, [{', '.join(f'[{pt(cc)}, {pt(e)}]' for cc, e in sg)}]]"


Path("ts/src/body-adult-foot-lines-data.ts").write_text(
    "// Generated by harness/franzi_feet/lines.py from ref/franzi/hands/feet-front.png. Do not edit by hand.\n"
    "// The foot's interior lines in the body's knot coordinates [v, d] (head heights, see body-adult-foot-data.ts), left foot.\n\n"
    'import type { Chain } from "./tables.ts";\n\n'
    "/** The dividers between toes, little toe to big toe, each from the base of the toes down to the notch in the outline. */\n"
    "export const FOOT_DIVIDERS: readonly Chain[] = [\n  " + ",\n  ".join(chain_ts(c) for c in dividers) + ",\n];\n\n"
    "/** The toenails, little toe to big toe, each a closed ring on its rim. */\n"
    "export const FOOT_NAILS: readonly Chain[] = [\n  " + ",\n  ".join(chain_ts(c) for c in nails) + ",\n];\n\n"
    "/** Each divider's thickness in head radii at nine evenly spaced points (thin at its base, heavy at the notch). */\n"
    "export const FOOT_DIVIDER_WIDTHS: readonly (readonly number[])[] = [\n  " + ",\n  ".join("[" + ", ".join(f"{w:.4f}" for w in ws) + "]" for ws in widths) + ",\n];\n"
)
print("wrote ts/src/body-adult-foot-lines-data.ts")
