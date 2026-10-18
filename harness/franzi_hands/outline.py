"""Trace the relaxed hand's outline from the close-up, in the body's own coordinates, and emit it as TypeScript.

    ./harness/run.sh harness/franzi_hands/locate.py
    ./harness/run.sh harness/franzi_hands/mapping.py
    ./harness/run.sh harness/franzi_hands/outline.py

Same method as harness/franzi_feet/outline.py. The close-up is flipped (mapping.py) and scaled onto ref 04; this is the viewer's-left hand (the
person's right), the viewer's-right hand is its mirror, as the body is. A point is [v, d]: d the depth in head heights below the chin
((y - 434) / 352 on ref 04), v the half-width from the centre line ((668.2 - x) / 352), so the render maps it with the same `place` as the arm.

The silhouette is the close-up's alpha with its holes filled: the dark wedge between the thumb and the curled fingers is transparent in the
close-up (a hole), but it is inside the hand, so it is drawn as a dark shape (cavity, lines.py), not left as a hole in the outline. The outline is
inset by the render's half stroke like the arm's knots, so the stroke's outer edge lands on the skin's edge. From D_CUT the hand takes over from
the arm's knots, blended over D_CUT to D_BLEND (the close-up's forearm is a few px different in width from the arm's, and a fixed switch would
show as a notch), then round the fingers and back up the inner side to the same depth. Writes out/franzi_hands/hand.json and
ts/src/body-adult-hand-data.ts (HAND_OUTLINE: an open chain from the outer edge at D_CUT, round the fingers, to the inner edge).
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/franzi_hands")
H, CX, CHIN = 352.0, 668.2, 434.0
HS_H = 0.008
# The close-up starts at d 1.99 (its top row lands on y 1134), so there is nothing above D_CUT to blend with; the blend is short because the arm's
# knots widen into the reference's outer corner at the hand (v 0.84 at d 2.3) where the close-up's hand is narrower, and a long blend dragged the
# outer edge outside the skin (found with view.py).
D_CUT, D_BLEND = 2.00, 2.16
TOL = 0.0022
M = json.load(open(OUT / "mapping.json"))
s, dx, dy = M["s"], M["dx"], M["dy"]
W = M["W"]
c = np.array(Image.open("ref/franzi/hands/relaxed.png").convert("RGBA"))[..., 3] > 128
cf = c[:, ::-1]
sil = ndimage.binary_fill_holes(cf)
cavity = sil & ~cf
print("silhouette %d px, holes (the cavity) %d px" % (sil.sum(), cavity.sum()))
np.save(OUT / "silhouette.npy", sil)
np.save(OUT / "cavity.npy", cavity)

# The fingers' tips are separated by gaps narrower than two half strokes (2 x 22 close-up px), which followed as outline draw as heavy lobes (the
# first version did, as the toes did). Gaps under 2 * CLOSE_R px are closed, so the outline keeps the stepped fingertips, and the separations are
# drawn as thin lines instead (lines.py).
CLOSE_R = 60
disc = np.hypot(*np.mgrid[-CLOSE_R : CLOSE_R + 1, -CLOSE_R : CLOSE_R + 1]) <= CLOSE_R
sil = ndimage.binary_closing(np.pad(sil, CLOSE_R + 2), structure=disc)[CLOSE_R + 2 : -(CLOSE_R + 2), CLOSE_R + 2 : -(CLOSE_R + 2)]
np.save(OUT / "silhouette_closed.npy", sil)
# what the closing added: the gaps between the fingertips (and the notch by the thumb's tip), drawn by lines.py as thin dark wedges so the fingers still read
np.save(OUT / "gaps.npy", sil & ~ndimage.binary_fill_holes(cf))
r_cc = HS_H * H / s
sd = ndimage.distance_transform_edt(sil) - ndimage.distance_transform_edt(~sil)
sd = ndimage.gaussian_filter(sd, 2.5)
inset = sd > r_cc
cut_row = int(round((CHIN + D_CUT * H - dy) / s))
blob = inset.copy()
blob[:cut_row] = False
lab, n = ndimage.label(blob)
blob = lab == lab[cut_row + 60, int(np.nonzero(blob[cut_row + 60])[0].mean())]
pts = np.array(tl.boundary(blob), float)
top = pts[:, 1] <= cut_row + 1.5
keep = np.nonzero(~top)[0]
runs, cur = [], [keep[0]]
for i in keep[1:]:
    if i == cur[-1] + 1:
        cur.append(i)
    else:
        runs.append(cur)
        cur = [i]
runs.append(cur)
if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(pts) - 1:
    runs[0] = runs[-1] + runs[0]
    runs.pop()
path = pts[max(runs, key=len)]
if path[0, 0] > path[-1, 0]:
    path = path[::-1]
print("outline path: %d boundary px, from (%.0f, %.0f) to (%.0f, %.0f) in close-up px" % (len(path), *path[0], *path[-1]))

body = open("ts/src/body-adult-data.ts").read()


def table(name):
    m = re.search(r"export const %s[^=]*=\s*(\[\[.*?\]\]);" % name, body, re.S)
    return np.array(json.loads(m.group(1)))


arm_o, arm_i = table("ARM_OUTER"), table("ARM_INNER")
x04 = path[:, 0] * s + dx
y04 = path[:, 1] * s + dy
d = (y04 - CHIN) / H
v = (CX - x04) / H
inner_start = int(np.argmax(d))  # the lowest point is a fingertip; the outer edge comes before it, the inner edge after
side = np.zeros(len(d), int)
side[inner_start:] = 1


def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


v_b = v.copy()
for i in range(len(d)):
    if d[i] >= D_BLEND:
        continue
    t = smoothstep((d[i] - D_CUT) / (D_BLEND - D_CUT))
    knot = np.interp(d[i], arm_o[:, 0], arm_o[:, 1]) - HS_H if side[i] == 0 else np.interp(d[i], arm_i[:, 0], arm_i[:, 1]) + HS_H
    v_b[i] = (1 - t) * knot + t * v[i]
d_b = d.copy()
v_b[0] = np.interp(D_CUT, arm_o[:, 0], arm_o[:, 1]) - HS_H
d_b[0] = D_CUT
v_b[-1] = np.interp(D_CUT, arm_i[:, 0], arm_i[:, 1]) + HS_H
d_b[-1] = D_CUT
arr = np.stack([v_b, d_b], 1)
arr[1:-1, 0] = ndimage.gaussian_filter1d(arr[:, 0], 5.0, mode="nearest")[1:-1]
arr[1:-1, 1] = ndimage.gaussian_filter1d(arr[:, 1], 5.0, mode="nearest")[1:-1]
xy = [tuple(p) for p in arr]
start, segs = tl.fit_chain(xy, tl.simplify(xy, TOL))
print("hand outline: %d segments, from [v %.4f, d %.4f] to [v %.4f, d %.4f]; lowest point d %.4f" % (len(segs), *start, *segs[-1][1], arr[:, 1].max()))
json.dump({"chain": [list(start), [[list(a), list(b)] for a, b in segs]], "D_CUT": D_CUT, "D_BLEND": D_BLEND}, open(OUT / "hand.json", "w"))


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


body_ts = ", ".join(f"[{pt(cc)}, {pt(e)}]" for cc, e in segs)
Path("ts/src/body-adult-hand-data.ts").write_text(
    "// Generated by harness/franzi_hands/outline.py from ref/franzi/hands/relaxed.png. Do not edit by hand.\n"
    "// The relaxed hand's outline in the body's knot coordinates [v, d] (v the half-width and d the depth below the chin, both in head heights),\n"
    "// inset by the render's half stroke like the arm knots: an open chain from the outer edge at HAND_D_CUT, round the fingers, to the inner edge.\n\n"
    'import type { Chain } from "./tables.ts";\n\n'
    f"/** Where the arm ends and the hand begins, in head heights below the chin. */\nexport const HAND_D_CUT = {D_CUT};\n\n"
    f"/** The relaxed hand, viewer's-left (the person's right), outer edge to inner edge; the other hand is its mirror, walked the other way. */\nexport const HAND_OUTLINE: Chain = [{pt(start)}, [{body_ts}]];\n"
)
print("wrote ts/src/body-adult-hand-data.ts")
