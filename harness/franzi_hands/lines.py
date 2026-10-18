"""The relaxed hand's interior: the shaded fingers, the cavity, the nails and the contour lines, traced from the close-up.

    ./harness/run.sh harness/franzi_hands/lines.py

Everything is read off the flipped close-up (mapping.py) and written in the body's knot coordinates [v, d] (see outline.py), for the viewer's-left
hand; the other is its mirror.

shade    the second-tone fingers: the curled fingers that lie in shadow. Lit skin is lightness 205 to 220 and the shaded part 150 to 190 (a histogram
         of the hand has exactly those two bulks), so the mask is the hand's pixels in 140 to 196, below row SHADE_FROM (above it the same band is
         the thin shading along the inner edge of the forearm and the back of the hand, which the outline carries), opened so thin edges fall away,
         and kept where large.
cavity   the dark wedge between the thumb and the curled fingers. It is transparent in the close-up (a hole in the silhouette, filled by outline.py);
         here it is the hole itself, drawn as a dark shape inside the hand.
nails    the rim of each nail, from Grok's nail cut-outs (locate.py), smoothed.
lines    the dark contour lines (lightness under 115, a few px wide) that divide the thumb, the palm and the fingers: each connected piece is thinned
         to a centre line by taking, along its main direction, the median position in short bins, kept when long enough, and given a thickness
         measured across it. Tapered like the foot's dividers.

Writes out/franzi_hands/lines.json and ts/src/body-adult-hand-lines-data.ts.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/franzi_hands")
H, CX, CHIN = 352.0, 668.2, 434.0
S_RAD = 175.7
M = json.load(open(OUT / "mapping.json"))
s, dx, dy = M["s"], M["dx"], M["dy"]
SHADE_FROM = 780
img = np.array(Image.open("ref/franzi/hands/relaxed.png").convert("RGBA")).astype(float)[:, ::-1]
lum = img[..., :3].mean(2)
alpha = img[..., 3] > 128
sil = np.load(OUT / "silhouette.npy")
cavity = np.load(OUT / "cavity.npy")
L = np.load(OUT / "layers.npz")


def flip(m):
    return m[:, ::-1]


def to_body(x, y):
    return ((CX - (x * s + dx)) / H, ((y * s + dy) - CHIN) / H)


def fit_mask(mask, blur, tol, step=None, min_px=200):
    """Closed chains of every large component of `mask`, smoothed along the edge, in body coordinates."""
    out = []
    lab, n = ndimage.label(mask)
    for i in range(1, n + 1):
        c = lab == i
        if c.sum() < min_px:
            continue
        pts = np.array(tl.boundary(c), float)
        sm = np.stack([ndimage.gaussian_filter1d(pts[:, j], blur, mode="wrap") for j in (0, 1)], 1)
        body = [to_body(x, y) for x, y in sm]
        out.append(tl.fit_closed(body, tol))
    return out


# --- shaded fingers
band = alpha & (lum >= 140) & (lum <= 196)
band[:SHADE_FROM] = False
band = ndimage.binary_opening(band, structure=np.ones((9, 9)))
band = ndimage.binary_closing(band, structure=np.ones((9, 9)))
# fill the gaps between the fingertips that the outline closes (outline.py, CLOSE_R), so the shade and the outline agree at the tips
CLOSE_R = 14
disc = np.hypot(*np.mgrid[-CLOSE_R : CLOSE_R + 1, -CLOSE_R : CLOSE_R + 1]) <= CLOSE_R
band = ndimage.binary_closing(np.pad(band, CLOSE_R + 2), structure=disc)[CLOSE_R + 2 : -(CLOSE_R + 2), CLOSE_R + 2 : -(CLOSE_R + 2)] & np.load(OUT / "silhouette_closed.npy")
lab, n = ndimage.label(band)
sizes = ndimage.sum(band, lab, range(1, n + 1))
shade = np.isin(lab, [i + 1 for i, z in enumerate(sizes) if z > 8000])
print("shade: %d components kept of %d, %d px" % (int((sizes > 8000).sum()), n, int(shade.sum())))
shade_ch = fit_mask(shade, 4.0, 0.0035, min_px=8000)
cav_ch = fit_mask(cavity, 3.0, 0.003, min_px=2000)
print("shade chains %d (segments %s), cavity chains %d (segments %s)" % (len(shade_ch), [len(c[1]) for c in shade_ch], len(cav_ch), [len(c[1]) for c in cav_ch]))

# --- nails
nails = []
for k in ("nail_1", "nail_2", "nail_3", "nail_4"):
    m = flip(L[k])
    m = ndimage.binary_fill_holes(m)
    if k == "nail_1":
        # The outline is inset by half a stroke on the thumb's inner side but the nail is not, so the nail sat against the outline and the stroke covered
        # its edge. Moved toward the thumb's middle by that half stroke and shrunk by a tenth, about its centre.
        ys_, xs_ = np.nonzero(m)
        cy_, cx_ = ys_.mean(), xs_.mean()
        shift = -0.5 * json.load(open(OUT / "hand.json"))["K"] * 0.008 * H / s  # half the hand stroke's half width
        m = ndimage.affine_transform(m.astype(float), [1 / 0.9, 1 / 0.9], offset=[cy_ - cy_ / 0.9, cx_ - cx_ / 0.9 - shift], order=1) > 0.5
    ch = fit_mask(m, 2.5, 0.0025, min_px=300)
    nails += ch
print("nails: %d chains" % len(nails))

# --- the gaps the outline closed between the fingertips, as dark wedges; and each finger piece (Grok's cut-outs of the four fingers) as a closed shape, to
# be drawn with a thin outline of its own, so the separations between the curled fingers show. (Without them the shaded fingers were one flat blob.)
# narrowed by 8 px so the wedges are slits, as the reference's are, not the full closed gap
gaps = fit_mask(ndimage.binary_erosion(np.load(OUT / "gaps.npy"), iterations=8), 3.0, 0.003, min_px=300)
fingers = []
# finger_4, the long lit finger, is left out: its piece has a ragged top edge where Grok cut it from the back of the hand (it drew a wiggly line across it),
# and its separation from the shaded fingers is the traced "edge" line already
for k in ("finger_1", "finger_2", "finger_3"):
    fingers += fit_mask(ndimage.binary_fill_holes(flip(L[k])), 3.0, 0.0025, min_px=3000)
print("gaps: %d chains, fingers: %d chains" % (len(gaps), len(fingers)))

# --- contour lines: hand-placed points snapped onto the drawn dark line, see trace_lines.py (the automatic finder caught only fragments of them)
sys.path.insert(0, "harness/franzi_hands")
import trace_lines as tr  # noqa: E402

lines, widths = [], []
for name, pts in tr.LINES.items():
    out, _, on = tr.snap(pts)
    body = [to_body(x, y) for x, y in out[::2]]
    start, segs = tl.fit_chain(body, tl.simplify(body, 0.0016))
    lines.append((start, segs))
    widths.append([float(w * s / S_RAD) for w in tr.width(out)])  # thickness in head radii on ref 04
    print(f"line {name:8s}: {len(segs)} segments, {100 * (on < tr.ON_RIDGE).mean():.0f}% on a ridge")


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


def chain_ts(c):
    st, sg = c
    return f"[{pt(st)}, [{', '.join(f'[{pt(cc)}, {pt(e)}]' for cc, e in sg)}]]"


def chains_ts(name, doc, chains):
    if not chains:  # an empty list needs no body (a bare "[\n  ,\n]" does not typecheck)
        return f"/** {doc} */\nexport const {name}: readonly Chain[] = [];\n\n"
    return f"/** {doc} */\nexport const {name}: readonly Chain[] = [\n  " + ",\n  ".join(chain_ts(c) for c in chains) + ",\n];\n\n"


json.dump({"n_lines": len(lines)}, open(OUT / "lines.json", "w"))
Path("ts/src/body-adult-hand-lines-data.ts").write_text(
    "// Generated by harness/franzi_hands/lines.py from ref/franzi/hands/relaxed.png. Do not edit by hand.\n"
    "// The relaxed hand's interior in the body's knot coordinates [v, d] (head heights, see body-adult-hand-data.ts), viewer's-left hand.\n\n"
    'import type { Chain } from "./tables.ts";\n\n'
    + chains_ts("HAND_SHADE", "The curled fingers in shadow, drawn in a second tone of the skin.", shade_ch)
    + chains_ts("HAND_CAVITY", "The dark wedge between the thumb and the curled fingers.", cav_ch)
    + chains_ts("HAND_GAPS", "The gaps between the fingertips that the outline closes, drawn as dark wedges.", gaps)
    + chains_ts("HAND_FINGERS", "The three shaded finger pieces (the curled fingers), each closed, drawn with a thin outline of its own.", fingers)
    + chains_ts("HAND_NAILS", "The visible nails, thumb first: closed rings with a lighter fill.", nails)
    + chains_ts("HAND_LINES", "The contour lines, open chains snapped onto the drawn dark lines: the long outer line, the line down between the shaded fingers, the finger separation.", lines)
    + "/** Each contour line's thickness in head radii at nine evenly spaced points. */\nexport const HAND_LINE_WIDTHS: readonly (readonly number[])[] = [\n  "
    + ",\n  ".join("[" + ", ".join(f"{w:.4f}" for w in ws) + "]" for ws in widths)
    + ",\n];\n"
)
print("wrote ts/src/body-adult-hand-lines-data.ts")
