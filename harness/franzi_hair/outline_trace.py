"""Fit the outline regions of outline_masks.py into chains in head radii, and emit them as TypeScript.

    ./harness/run.sh harness/franzi_hair/outline_masks.py
    ./harness/run.sh harness/franzi_hair/outline_trace.py

Same calibration as trace.py (origin x 660, origin y 270.5, 175.7 reference px per head radius). Writes out/franzi_hair/outline.json
(name -> list of closed chains, for outline_view.py) and ts/src/body-adult-outline-data.ts.

Where a chain sits relative to the edge matters, because the stroke is drawn centred on it:
    face, strips, ears   the reference draws a black line just outside the skin, so the chain is grown 2 px onto that line's centre
    sil (hair)           the hair has no drawn line, only its own edge, so the chain is shrunk 1 px: the stroke's outer edge, not its
                         centre, then lands on the edge (the stroke is about 2.5 px wide)
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OX, OY, S = 660.0, 270.5, 175.7
TOL = 0.01
m = np.load("out/franzi_hair/outline_masks.npz")


def to_r(pts):
    return [((x - OX) / S, (y - OY) / S) for x, y in pts]


def components(mask, min_px):
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        c = lab == i
        if c.sum() >= min_px:
            out.append(c)
    return sorted(out, key=lambda c: -c.sum())


def fit(mask, grow, blur, tol=TOL, min_px=40):
    """The closed chains of every component of `mask`, grown (or, negative, shrunk) by `grow` px and smoothed."""
    f = ndimage.gaussian_filter(mask.astype(float), blur) if blur else mask.astype(float)
    # growing the edge by g px is a threshold of Phi(-g / sigma) on the blurred field (Phi the normal CDF), and shrinking it the same
    # with the sign turned; with no blur the threshold stays at one half
    level = 0.5 * (1 + math.erf(-grow / (blur * math.sqrt(2)))) if blur else 0.5
    out = []
    for c in components(f > level, min_px):
        out.append(tl.fit_closed(to_r(tl.boundary(c)), tol))
    return out


SIL_SIGMA_HI, SIL_SIGMA_LO, SIL_STEP, SIL_KEEP = 7.0, 2.0, 7.0, 2.5


def fit_smooth(mask, shift=-1, min_px=150, sigma_hi=None, step=None):
    """Closed chains whose slope is continuous at every join, for the hair silhouette.

    The hair's edge is the edge of an AI segmentation: ragged at the pixel scale, and fitted with the least number of quadratics that
    stay within 2 px it came out as 90 short curves meeting at kinks (81 of 89 joins over 10 degrees), which reads as wobble. Here the
    edge is low-passed along its length (sigma SIL_SIGMA_HI px), except where that would move it more than SIL_KEEP px off the real
    edge: there a tip or a narrow lock is being rounded off, so the light smoothing (SIL_SIGMA_LO) is blended in (full below 1.5 px of
    movement, none above SIL_KEEP + 1.5). The result is resampled every SIL_STEP px and drawn as a quadratic B-spline: the curve runs
    through the midpoints of the polygon's sides with each vertex as a control point, so the slope cannot jump at a join.
    """
    sig_hi = sigma_hi or SIL_SIGMA_HI
    out = []
    moved = ndimage.binary_erosion(mask, iterations=-shift) if shift < 0 else ndimage.binary_dilation(mask, iterations=shift) if shift > 0 else mask
    for c in components(moved, min_px):
        pts = np.array(tl.boundary(c), float)
        n = len(pts)
        tree = cKDTree(pts)

        def smooth(sig):
            return np.stack([ndimage.gaussian_filter1d(pts[:, j], sig, mode="wrap") for j in (0, 1)], 1)

        hi, lo = smooth(sig_hi), smooth(SIL_SIGMA_LO)
        d = tree.query(hi)[0]
        w = np.clip((d - SIL_KEEP + 1.5) / 3.0, 0, 1)[:, None]  # 0 where the smooth edge is within SIL_KEEP - 1.5 px of the real one
        sm = (1 - w) * hi + w * lo
        seg = np.hypot(*np.diff(np.vstack([sm, sm[:1]]), axis=0).T)
        arc = np.concatenate([[0], np.cumsum(seg)])
        m = max(8, int(round(arc[-1] / (step or SIL_STEP))))
        t = np.linspace(0, arc[-1], m, endpoint=False)
        verts = np.stack([np.interp(t, arc, np.append(sm[:, j], sm[0, j])) for j in (0, 1)], 1)
        q = np.array(to_r([tuple(v) for v in verts]))
        mid = (q + np.roll(q, -1, axis=0)) / 2
        start = tuple(mid[0])
        segs = [(tuple(q[(i + 1) % m]), tuple(mid[(i + 1) % m])) for i in range(m)]
        out.append((start, segs))
        print(f"  smooth chain: {n} edge px, {m} vertices, max smooth-vs-real edge distance {tree.query(sm)[0].max():.1f} px")
    return out


res = {
    "face": fit_smooth(m["face"], shift=2, min_px=2000, sigma_hi=5.0),
    "strips": fit_smooth(m["strips"], shift=0, min_px=60, sigma_hi=2.0, step=3.0),
    "ear_l": fit_smooth(m["ear_l"], shift=1, min_px=100, sigma_hi=2.2, step=3.5),
    "ear_r": fit_smooth(m["ear_r"], shift=1, min_px=100, sigma_hi=2.2, step=3.5),
    "neckfill": fit_smooth(m["neckfill"], shift=0, min_px=300, sigma_hi=3.0, step=4.0),
    "concha_l": fit_smooth(m["concha_l"], shift=0, min_px=30, sigma_hi=2.0, step=3.0),
    "concha_r": fit_smooth(m["concha_r"], shift=0, min_px=30, sigma_hi=2.0, step=3.0),
    "sil": fit_smooth(m["sil"], shift=-1),
}
json.dump(res, open("out/franzi_hair/outline.json", "w"), default=lambda o: list(o))
for k, v in res.items():
    print(f"{k:7s} chains {len(v)}  segments {[len(c[1]) for c in v]}")


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


def chain(c):
    st, sg = c
    return f"[{pt(st)}, [{', '.join(f'[{pt(cc)}, {pt(e)}]' for cc, e in sg)}]]"


doc = {
    "face": "The visible skin of the face: forehead, cheeks, chin, filled across the eyes and brows. Its edge is the hairline, the curtains' inner edges and the jaw.",
    "strips": "Small skin regions beside the face (the side of the neck under each ear), each running a few pixels under the face.",
    "ear_l": "The visible skin of the left ear.",
    "ear_r": "The visible skin of the right ear.",
    "neckfill": "Skin between the jaw, the hair edge and the shoulder, drawn behind the hair with no outline.",
    "concha_l": "The shaded inner part of the left ear, a second tone drawn over the ear.",
    "concha_r": "The shaded inner part of the right ear, a second tone drawn over the ear.",
    "sil": "The hair silhouette: every visible hair pixel plus the face, ears and strips shrunk a few pixels, so its edge only ever meets the page, the neck or the shoulder.",
}
parts = [
    "// Generated by harness/franzi_hair/outline_trace.py from outline_masks.py (the regions of ref/franzi/ 04). Do not edit by hand.\n"
    "// Head radii from the head centre, the calibration in harness/franzi_hair/trace.py (175.7 reference px per radius).\n\n"
    'import type { Chain } from "./tables.ts";\n'
]
for key, name in (("face", "ADULT_SKIN_FACE"), ("strips", "ADULT_SKIN_STRIPS"), ("ear_l", "ADULT_SKIN_EAR_L"), ("ear_r", "ADULT_SKIN_EAR_R"), ("neckfill", "ADULT_SKIN_NECKFILL"), ("concha_l", "ADULT_EAR_CONCHA_L"), ("concha_r", "ADULT_EAR_CONCHA_R"), ("sil", "ADULT_HAIR_SILHOUETTE")):
    body = ",\n  ".join(chain(c) for c in res[key])
    parts.append(f"/** {doc[key]} */\nexport const {name}: readonly Chain[] = [\n  {body},\n];\n")
Path("ts/src/body-adult-outline-data.ts").write_text("\n".join(parts))
print("wrote ts/src/body-adult-outline-data.ts")
