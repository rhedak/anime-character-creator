"""Trace the jacket's body (not its sleeves) off katherina_grok.jpg.

    ./harness/run.sh harness/clothes/trace_jacket.py

Each side of the jacket is one piece: the navy upper panel, carried down under
the belt into the lower panel that flares from it. What hides it, and how each
hidden stretch is carried:

- The sleeves share components 179/180 with the upper panels, with no outline
  between; they are purple where the panels are navy, so each pixel is split by
  hue (red above green is the sleeve's purple). The sleeves are C4's.
- The hair covers the upper panels' outer edges from the shoulder to the
  armpit. The panel there is the convex hull of its own visible navy, which
  carries the shoulder line and the side seam straight across the hair; any
  body a cut is worn on puts its own hair over that stretch too.
- The belt covers the join. Its rows are bridged edge to edge, measured just
  above and just below it (the staff's shaft behind the fist, again).

The seam lines are the outline-dark ink inside each upper panel's hull, away
from its boundary: where the sleeve's back meets the body.

Writes `out/clothes/jacket.json` (left piece, right piece, seam lines) and
`out/clothes/jacket_overlay.png`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".claude/skills/trace-reference"))
import trace_lib as tl  # noqa: E402

REF = Path(__file__).resolve().parents[3] / "time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OX, OY, SC = 650.0, 481.0, 173.7
OUT = Path("out/clothes")

rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
s = rgb.sum(2)
lab, _ = ndi.label(s > 60)
disk = ndi.generate_binary_structure(2, 1)
ROWS = np.arange(s.shape[0])[:, None]
COLS = np.arange(s.shape[1])[None, :]

BELT_TOP, BELT_BOT = 878, 925  # rows the belt covers, with its outline


def hull_mask(m: np.ndarray) -> np.ndarray:
    ys, xs = np.nonzero(m)
    h = ConvexHull(np.column_stack([xs, ys]))
    inside = np.ones(m.shape, bool)
    for a, bb, c in h.equations:
        inside &= a * COLS + bb * ROWS + c <= 0.5
    return inside


def edges(m: np.ndarray, rows: range) -> np.ndarray:
    out = []
    for y in rows:
        xs = np.nonzero(m[y])[0]
        if len(xs):
            out.append((xs.min(), xs.max()))
    return np.mean(out, axis=0)


result = {}
over = Image.fromarray(np.clip(rgb * 3.0, 0, 255).astype("uint8"))
d = ImageDraw.Draw(over)
for side, upper_id, lower_id in (("left", 180, 203), ("right", 179, 202)):
    comp = lab == upper_id
    navy = comp & ~(r > g + 3)
    navy = ndi.binary_opening(navy, disk, 2)
    navy &= ROWS < BELT_TOP  # the panel above the belt only
    # the sleeve's purple can leave navy specks out along the arm; keep the
    # panel's own blob
    nl, _ = ndi.label(navy)
    sizes = np.bincount(nl.ravel())
    sizes[0] = 0
    navy = nl == np.argmax(sizes)
    upper = hull_mask(navy) & (ROWS < BELT_TOP + 2)
    lower = ndi.binary_fill_holes(lab == lower_id)
    a0 = edges(upper, range(BELT_TOP - 10, BELT_TOP))
    b0 = edges(lower, range(BELT_BOT + 2, BELT_BOT + 12))
    bridge = np.zeros(s.shape, bool)
    y0, y1 = BELT_TOP - 4, BELT_BOT + 6
    for y in range(y0, y1):
        t = (y - y0) / (y1 - y0)
        lo, hi = (1 - t) * a0 + t * b0
        bridge[y, round(lo) : round(hi) + 1] = True
    piece = upper | bridge | lower
    piece = ndi.binary_fill_holes(ndi.binary_erosion(ndi.binary_dilation(piece, disk, 3), disk, 3))
    piece = ndi.binary_dilation(piece, disk, 3)
    pts = [((x - OX) / SC, (y - OY) / SC) for x, y in tl.boundary(piece)]
    start, segs = tl.fit_closed(pts, 0.010)
    result[side] = {"start": start, "segs": segs}
    d.line([(OX + x * SC, OY + y * SC) for x, y in tl.sample_chain(start, segs, 10)], fill="#00ff66", width=2)
    print(side, "segments", len(segs), "navy px", int(navy.sum()))

    # seam line: dark ink inside the upper hull, well away from its boundary
    inner = ndi.binary_erosion(upper, disk, 8)
    ink = inner & (s <= 60) & ~ndi.binary_dilation(lab == 8, disk, 4)
    il, n = ndi.label(ink, structure=np.ones((3, 3)))
    lines = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(il == i)
        # The collar's own outline runs inside the hull's top corner; the
        # seams are the long vertical strokes below it.
        if len(xs) < 60 or ys.mean() < 730:
            continue
        pts2 = np.column_stack([xs, ys]).astype(float)
        mu = pts2.mean(0)
        u = np.linalg.svd(pts2 - mu, full_matrices=False)[2][0]
        order = np.argsort((pts2 - mu) @ u)
        bins = np.array_split(order, 6)
        cl = [pts2[order[0]], *[pts2[bb].mean(0) for bb in bins if len(bb)], pts2[order[-1]]]
        h = [((x - OX) / SC, (y - OY) / SC) for x, y in cl]
        st, sg = tl.fit_chain(h, [0, len(h) // 2, len(h) - 1])
        lines.append({"start": st, "segs": sg, "px": len(xs)})
        d.line([(OX + x * SC, OY + y * SC) for x, y in tl.sample_chain(st, sg, 10)], fill="#ff2255", width=2)
    result[side + "_lines"] = lines
    print(side, "seam lines", [ln["px"] for ln in lines])

json.dump(result, open(OUT / "jacket.json", "w"), indent=1)
over.crop((360, 640, 940, 1080)).resize((1160, 880)).save(OUT / "jacket_overlay.png")
