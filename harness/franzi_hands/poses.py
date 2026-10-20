"""Trace the open palm and the fist from the close-ups, in the arm's own hanging frame, and emit them as TypeScript.

    ./harness/run.sh harness/franzi_hands/poses.py            both hands: writes out/franzi_hands/pose-*.json, pose-*-view.png and ts/src/body-adult-hand-poses-data.ts
    ./harness/run.sh harness/franzi_hands/poses.py open       one hand, without writing the TypeScript (to look at)

The relaxed hand (outline.py) is traced in the body's knot coordinates [v, d] (v the half-width from the centre line and d the depth below the chin, both in
head heights; the viewer's-left hand, the other is its mirror), hanging from the arm's wrist at d 2.0. These two are traced in the same frame, so that a posed arm
(body-adult-pose.ts) can take any of the three hands and turn it with the arm about the shoulder: the fingers hang down from the wrist, the thumb on the outer side
(the anatomical position: palm toward the viewer). The close-ups have the fingers up, so each is turned into that frame first:

    open-palm   shows a left hand, palm to the viewer, fingers up, thumb on the image's left. A vertical flip (a mirror: it becomes a right hand, the viewer's-left
                one) leaves the thumb on the image's left and the fingers down.
    fist        shows a right hand, palm side to the viewer, fingers up, the thumb on the image's right (wrapped over the fingers). A half turn puts the fingers down
                and the thumb on the left, the outer side of the viewer's-left hand.

Scale: all three close-ups share a generation scale (the open palm's wrist is 328 px wide, the relaxed hand's 331), so the open palm takes the relaxed hand's scale
(mapping.json, head heights per close-up px = s / 352) and the fist is scaled so that its wrist is as wide as the open palm's. The wrist row is where the hand starts to
widen going up the image, and it lands on d 2.057 (the relaxed hand's wrist, ref 04 row 1158), centred on the arm's v 0.7165. Everything else is the relaxed hand's method:
the silhouette with its holes filled, narrow gaps between the fingertips closed (the separations are drawn as lines), an inset by the hand's half stroke, the boundary from
the cut at d 2.0 round the fingers to the cut on the inner side, blended into the arm's knots over D_CUT to D_BLEND, smoothed, and fitted as an open quadratic B-spline.
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/franzi_hands")
H, CHIN = 352.0, 434.0
HS_H = 0.008
HAND_K = 0.33
HS_HAND = HAND_K * HS_H
D_CUT, D_BLEND = 2.00, 2.16
D_WRIST = (1158 - CHIN) / H  # the relaxed hand's wrist, ref 04 row 1158
V_WRIST = (668.2 - 416.0) / H  # and its centre line, ref 04 x 416
M = json.load(open(OUT / "mapping.json"))
K_RELAXED = M["s"] / H  # head heights per close-up px
SIG, STEP = 4.0, 0.0018
CLOSE_R = 14

body = open("ts/src/body-adult-data.ts").read()


def table(name):
    m = re.search(r"export const %s[^=]*=\s*(\[\[.*?\]\]);" % name, body, re.S)
    return np.array(json.loads(m.group(1)))


ARM_O, ARM_I = table("ARM_OUTER"), table("ARM_INNER")

HANDS = {
    # name: (image, transform to the hanging frame, wrist width target source)
    "open": ("open-palm", lambda a: a[::-1, :]),
    "fist": ("fist", lambda a: a[::-1, ::-1]),
}


def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def wrist_of(sil):
    """The wrist: the narrowest row of the forearm, in the first 450 rows of the turned image (the forearm widens away from the hand, as the close-ups' arms do)."""
    w = ndimage.gaussian_filter1d(sil.sum(1).astype(float), 8)
    top = int(np.nonzero(sil.any(1))[0].min())
    y = top + int(np.argmin(w[top : top + 450]))
    return int(y), float(w[y])


def trace(name, write):
    img, tf = HANDS[name]
    a = np.array(Image.open(f"ref/franzi/hands/{img}.png").convert("RGBA"))[..., 3] > 128
    a = tf(a)
    sil0 = ndimage.binary_fill_holes(a)
    yw, wmin = wrist_of(sil0)
    ys = np.nonzero(sil0.any(1))[0]
    xs_w = np.nonzero(sil0[yw])[0]
    xw = (xs_w.min() + xs_w.max()) / 2
    # scale: the relaxed hand's, matched on the forearm width for the fist
    k = K_RELAXED if name == "open" else None
    if name == "fist":
        wopen = _FOREARM["open"]
        k = K_RELAXED * wopen / wmin
    _FOREARM[name] = wmin
    print(f"{name}: wrist row {yw}, centre x {xw:.0f}, forearm {wmin:.0f} px -> {wmin * k:.4f} H, scale {k:.6f} H/px, hand to the lowest finger {(ys.max() - yw) * k:.3f} H")
    # close narrow gaps between the fingertips (the separations are lines), as the relaxed hand's
    disc = np.hypot(*np.mgrid[-CLOSE_R : CLOSE_R + 1, -CLOSE_R : CLOSE_R + 1]) <= CLOSE_R
    sil = ndimage.binary_closing(np.pad(sil0, CLOSE_R + 2), structure=disc)[CLOSE_R + 2 : -(CLOSE_R + 2), CLOSE_R + 2 : -(CLOSE_R + 2)]
    r_cc = HS_HAND / k
    sd = ndimage.distance_transform_edt(sil) - ndimage.distance_transform_edt(~sil)
    sd = ndimage.gaussian_filter(sd, 2.5)
    inset = sd > r_cc
    cut_row = int(round(yw + (D_CUT - D_WRIST) / k))
    blob = inset.copy()
    blob[:cut_row] = False
    lab, n = ndimage.label(blob)
    seed_y = cut_row + 60
    blob = lab == lab[seed_y, int(np.nonzero(blob[seed_y])[0].mean())]
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
    # to knot coordinates: d grows down the image from the wrist, v is positive to the image's left (the viewer's-left hand's outer side)
    d = D_WRIST + (path[:, 1] - yw) * k
    v = V_WRIST - (path[:, 0] - xw) * k
    inner_start = int(np.argmax(d))
    side = np.zeros(len(d), int)
    side[inner_start:] = 1
    v_b = v.copy()
    for i in range(len(d)):
        if d[i] >= D_BLEND:
            continue
        t = smoothstep((d[i] - D_CUT) / (D_BLEND - D_CUT))
        knot = np.interp(d[i], ARM_O[:, 0], ARM_O[:, 1]) - HS_H if side[i] == 0 else np.interp(d[i], ARM_I[:, 0], ARM_I[:, 1]) + HS_H
        v_b[i] = (1 - t) * knot + t * v[i]
    d_b = d.copy()
    v_b[0] = np.interp(D_CUT, ARM_O[:, 0], ARM_O[:, 1]) - HS_H
    d_b[0] = D_CUT
    v_b[-1] = np.interp(D_CUT, ARM_I[:, 0], ARM_I[:, 1]) + HS_H
    d_b[-1] = D_CUT
    arr = np.stack([v_b, d_b], 1)
    sm = arr.copy()
    sm[1:-1, 0] = ndimage.gaussian_filter1d(arr[:, 0], SIG, mode="nearest")[1:-1]
    sm[1:-1, 1] = ndimage.gaussian_filter1d(arr[:, 1], SIG, mode="nearest")[1:-1]
    seg = np.hypot(*np.diff(sm, axis=0).T)
    arc = np.concatenate([[0], np.cumsum(seg)])
    m = max(10, int(round(arc[-1] / STEP)))
    tpos = np.linspace(0, arc[-1], m)
    verts = np.stack([np.interp(tpos, arc, sm[:, 0]), np.interp(tpos, arc, sm[:, 1])], 1)
    start = tuple(verts[0])
    segs = []
    for i in range(1, len(verts) - 1):
        end = tuple(verts[-1]) if i == len(verts) - 2 else tuple((verts[i] + verts[i + 1]) / 2)
        segs.append((tuple(verts[i]), end))
    print(f"{name}: outline {len(segs)} segments, lowest point d {sm[:, 1].max():.4f}, v range {sm[:, 0].min():.3f} to {sm[:, 0].max():.3f}")
    chain = [list(start), [[list(c), list(e)] for c, e in segs]]
    json.dump({"chain": chain, "D_CUT": D_CUT, "D_BLEND": D_BLEND, "k": k, "yw": yw, "xw": float(xw)}, open(OUT / f"pose-{name}.json", "w"))
    view(name, a, sil0, k, yw, xw, chain)
    return chain


def chain_points(chain, per=6):
    start, segs = chain
    pts = [tuple(start)]
    p0 = np.array(start)
    for c, e in segs:
        c, e = np.array(c), np.array(e)
        for t in np.linspace(0, 1, per + 1)[1:]:
            pts.append(tuple((1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t**2 * e))
        p0 = e
    return pts


def view(name, a, sil0, k, yw, xw, chain):
    """The traced outline (red) over the turned close-up, at 1 px per 1/k... drawn in the close-up's own pixels."""
    pts = [((V_WRIST - v) / k + xw, (d - D_WRIST) / k + yw) for v, d in chain_points(chain)]
    im = Image.fromarray((np.where(a, 220, 40)).astype(np.uint8)).convert("RGB")
    dr = ImageDraw.Draw(im)
    dr.line(pts, fill=(230, 30, 30), width=3)
    ys = np.nonzero(sil0.any(1))[0]
    im = im.crop((0, max(0, ys.min() - 20), im.width, min(im.height, ys.max() + 20)))
    im = im.resize((im.width // 2, im.height // 2))
    im.save(OUT / f"pose-{name}-view.png")


_FOREARM: dict = {}


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


def emit(chains):
    names = {"open": "HAND_OPEN_OUTLINE", "fist": "HAND_FIST_OUTLINE"}
    out = [
        "// Generated by harness/franzi_hands/poses.py from ref/franzi/hands/open-palm.png and fist.png. Do not edit by hand.",
        "// The open palm and the fist in the same frame as HAND_OUTLINE (body-adult-hand-data.ts): the body's knot coordinates [v, d] (v the half-width from the centre line, d the depth below",
        "// the chin, in head heights), the viewer's-left hand hanging from the wrist at d 2.0 with the fingers down and the thumb on the outer side, inset by the hand's half stroke, an open",
        "// chain from the outer edge at the wrist round the fingers to the inner edge. The other hand is its mirror. A posed arm turns one of them with the arm (body-adult-pose.ts).",
        "",
        'import type { Chain } from "./tables.ts";',
        "",
    ]
    for key, const in names.items():
        start, segs = chains[key]
        body_ts = ", ".join(f"[{pt(c)}, {pt(e)}]" for c, e in segs)
        what = "open palm" if key == "open" else "loose fist"
        out.append(f"/** The {what}, viewer's-left hand, outer edge to inner edge. */")
        out.append(f"export const {const}: Chain = [{pt(start)}, [{body_ts}]];")
        out.append("")
    Path("ts/src/body-adult-hand-poses-data.ts").write_text("\n".join(out))
    print("wrote ts/src/body-adult-hand-poses-data.ts")


if __name__ == "__main__":
    which = sys.argv[1:] or ["open", "fist"]
    res = {}
    for n in ["open", "fist"]:  # the fist's scale needs the open palm's forearm width
        if n in which or n == "open":
            res[n] = trace(n, False)
    if len(sys.argv) == 1:
        emit(res)
