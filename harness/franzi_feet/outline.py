"""Trace the foot's outline from the close-up, in the body's own coordinates, and emit it as TypeScript.

    ./harness/run.sh harness/franzi_feet/locate.py       # segment layers
    ./harness/run.sh harness/franzi_feet/mapping.py      # close-up onto ref 04
    ./harness/run.sh harness/franzi_feet/outline.py

The close-up's two feet are mirror twins (IoU 0.991 once one is mirrored onto the other), so the foot is the mean of foot A and the mirror of
foot B, which is symmetric like the rest of the body (every edge in body-adult-data.ts is the mean of the left and right). It is placed
with foot A's fit (mapping.py) and then centred on the mean of where the body's two feet stand.

Coordinates are the body knots' own: a point is [v, d], d the depth in head heights below the chin ((y - 434) / 352 on ref 04) and v the
half-width in head heights from the centre line ((|x - 668.2|) / 352), so the render maps it with the same `place` as the legs.

The knots are the ink's outer edge, stroke included, and the render insets the path by half a stroke (hs, 0.008 of a head height). The
foot is inset by the same amount here, so where it meets the legs there is no step. Above D_CUT the body path is the leg knots; from
D_CUT the foot takes over, blended from the knots to the traced foot over D_CUT to D_BLEND (the close-up's leg is 3 to 4 px narrower
than ref 04's at the ankle, and a fixed switch would show as a notch), then follows the traced outline round the toes and back up the inner
side to the same depth. Writes out/franzi_feet/foot.json and ts/src/body-adult-foot-data.ts (FOOT_OUTLINE, an open chain from the outer
edge at D_CUT, round the toes, to the inner edge at D_CUT).
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

OUT = Path("out/franzi_feet")
H, CX, CHIN = 352.0, 668.2, 434.0
HS_H = 0.008  # the render's half stroke in head heights (harness/franzi_feet/stroke.ts)
D_CUT, D_BLEND = 4.40, 4.85
XS = 1.06  # horizontal stretch of the foot about its centre line: the close-up's forefoot is 5% narrower across the toes than the body reference's feet (the gate allows 5%); 6% brings it to 4.3%
TOL = 0.0022

M = json.load(open(OUT / "mapping.json"))
c = np.array(Image.open("ref/franzi/hands/feet-front.png").convert("RGBA"))[..., 3] > 128
X = np.arange(c.shape[1])[None, :]
A, B = c & (X < 530), c & (X >= 540)

# --- the mean foot: A and the mirror of B, in A's frame
Bm = B[:, ::-1]
best = (0, 0, 0)
for dx in range(30, 70):
    for dy in range(-4, 5):
        sh = np.roll(np.roll(Bm, dx, axis=1), dy, axis=0)
        v = (A & sh)[560:1500].sum() / (A | sh)[560:1500].sum()
        if v > best[0]:
            best = (v, dx, dy)
print("foot A against the mirror of foot B: IoU %.4f (dx %d, dy %d)" % best)
_, mdx, mdy = best
Bsh = np.roll(np.roll(Bm, mdx, axis=1), mdy, axis=0)
mean = ndimage.gaussian_filter((A.astype(float) + Bsh.astype(float)) / 2, 1.5) > 0.5
ys_m, xs_m = np.nonzero(mean)
cx_m = xs_m.mean()
mean = ndimage.affine_transform(mean.astype(float), [1, 1 / XS], offset=[0, cx_m - cx_m / XS], order=1) > 0.5
# The toes touch, separated only by shadow lines; the slits between them are narrower than a stroke is wide and, followed as part of the
# outline, draw as teeth (the first version did). Slits under 2 * CLOSE_R px wide are closed, so the outline keeps the stepped toe lobes and the
# open gap beside the big toe (36 px at its top, narrowing to about 12 where two strokes would touch), and the toe separations are drawn as thin
# divider lines instead (lines.py). CLOSE_R was 11, which closed the lower half of that gap and left skin, with a short divider in it, between
# the big toe and its neighbour; 5 keeps the gap open as far down as a stroke can show it.
CLOSE_R = 5
disc = np.hypot(*np.mgrid[-CLOSE_R : CLOSE_R + 1, -CLOSE_R : CLOSE_R + 1]) <= CLOSE_R
mean = ndimage.binary_closing(np.pad(mean, CLOSE_R + 2), structure=disc)[CLOSE_R + 2 : -(CLOSE_R + 2), CLOSE_R + 2 : -(CLOSE_R + 2)]

# --- A's fit to ref 04, centred on the mean of the body's two feet
s, dx, dy = M["A"]["s"], M["A"]["dx"], M["A"]["dy"]
f = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA"))[..., 3] > 128
rows04 = slice(2150, 2300)
fl, fr = f.copy(), f.copy()
fl[:, 668:] = False
fr[:, :669] = False
cx_l = np.nonzero(fl[rows04])[1].mean()
cx_r = np.nonzero(fr[rows04])[1].mean()
half = ((CX - cx_l) + (cx_r - CX)) / 2
ys_, xs_ = np.nonzero(mean[int((2150 - dy) / s) : int((2300 - dy) / s)])
cx_mean_04 = xs_.mean() * s + dx
dx += (CX - half) - cx_mean_04
print("body feet centres %.1f and %.1f (mean half-distance %.1f px = %.4f H); foot A shifted to %.1f" % (cx_l, cx_r, half, half / H, CX - half))

# --- inset by the render's half stroke: a smoothed signed distance field, thresholded at the inset
r_cc = HS_H * H / s
sd = ndimage.distance_transform_edt(mean) - ndimage.distance_transform_edt(~mean)
sd = ndimage.gaussian_filter(sd, 2.5)
inset = sd > r_cc
cut_row = int(round((CHIN + D_CUT * H - dy) / s))
blob = inset.copy()
blob[:cut_row] = False
lab, n = ndimage.label(blob)
blob = lab == lab[cut_row + 40, int(np.nonzero(blob[cut_row + 40])[0].mean())]
pts = tl.boundary(blob)
pts = np.array(pts, float)
# drop the flat top, orient the loop so it starts at the outer (left) top corner and ends at the inner (right) one
top = pts[:, 1] <= cut_row + 1.5
keep = np.nonzero(~top)[0]
# the open path is the longest run of kept points around the loop
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

# --- to body coordinates [v, d], with the ankle blend toward the knots
body = open("ts/src/body-adult-data.ts").read()


def table(name):
    m = re.search(r"export const %s[^=]*=\s*(\[\[.*?\]\]);" % name, body, re.S)
    return np.array(json.loads(m.group(1)))


leg_o, leg_i = table("LEG_OUTER"), table("LEG_INNER")
x04 = path[:, 0] * s + dx
y04 = path[:, 1] * s + dy
d = (y04 - CHIN) / H
v = (CX - x04) / H  # the left foot: outer edge has the larger v
# which points belong to the outer side, which to the inner: split at the lowest point of the toes' centre line
mid = int(np.argmax(d))
side = np.zeros(len(d), int)  # 0 outer, 1 inner
side[mid:] = 1
# the foot is mirror-symmetric to itself nowhere, but the outer and inner halves meet at the lowest point; use the sole's middle instead
# (the big toe is the inner one, the little toes the outer, and the deepest point is the big toe's tip, on the inner half)
lowest_outer = int(np.argmin(np.abs(v - np.median(v))))  # unused guard
inner_start = int(np.argmax(d))  # deepest point: the big toe
side[:] = 0
side[inner_start:] = 1


def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


v_b = v.copy()
for i in range(len(d)):
    if d[i] >= D_BLEND:
        continue
    t = smoothstep((d[i] - D_CUT) / (D_BLEND - D_CUT))
    knot = np.interp(d[i], leg_o[:, 0], leg_o[:, 1]) - HS_H if side[i] == 0 else np.interp(d[i], leg_i[:, 0], leg_i[:, 1]) + HS_H
    v_b[i] = (1 - t) * knot + t * v[i]
# the path starts and ends exactly on the knots at D_CUT
v_b[0] = np.interp(D_CUT, leg_o[:, 0], leg_o[:, 1]) - HS_H
d_b = d.copy()
d_b[0] = D_CUT
v_b[-1] = np.interp(D_CUT, leg_i[:, 0], leg_i[:, 1]) + HS_H
d_b[-1] = D_CUT
xy = [(float(a), float(b)) for a, b in zip(v_b, d_b)]
# a light smoothing along the path, so the pixel stair-steps of the mask edge do not reach the fit
arr = np.array(xy)
arr[1:-1, 0] = ndimage.gaussian_filter1d(arr[:, 0], 6.0, mode="nearest")[1:-1]
arr[1:-1, 1] = ndimage.gaussian_filter1d(arr[:, 1], 6.0, mode="nearest")[1:-1]
xy = [tuple(p) for p in arr]
start, segs = tl.fit_chain(xy, tl.simplify(xy, TOL))
print("foot outline: %d segments, from [v %.4f, d %.4f] to [v %.4f, d %.4f]" % (len(segs), *start, *segs[-1][1]))
json.dump({"s": s, "dx": dx, "dy": dy, "chain": [list(start), [[list(a), list(b)] for a, b in segs]], "path_cc": path.tolist(), "D_CUT": D_CUT, "D_BLEND": D_BLEND}, open(OUT / "foot.json", "w"))


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


body_ts = ", ".join(f"[{pt(cc)}, {pt(e)}]" for cc, e in segs)
Path("ts/src/body-adult-foot-data.ts").write_text(
    "// Generated by harness/franzi_feet/outline.py from ref/franzi/hands/feet-front.png. Do not edit by hand.\n"
    "// The foot's outline in the body's knot coordinates [v, d] (v the half-width and d the depth below the chin, both in head heights),\n"
    "// inset by the render's half stroke like the leg knots: an open chain from the outer edge at D_CUT, round the toes, to the inner edge.\n\n"
    'import type { Chain } from "./tables.ts";\n\n'
    f"/** Where the legs end and the foot begins, in head heights below the chin. */\nexport const FOOT_D_CUT = {D_CUT};\n\n"
    f"/** The foot, left foot, outer edge to inner edge; the right foot is its mirror, walked the other way. */\nexport const FOOT_OUTLINE: Chain = [{pt(start)}, [{body_ts}]];\n"
)
print("wrote ts/src/body-adult-foot-data.ts")
