"""Trace the hanging sleeve and its cuff off katherina_grok.jpg, in an arm frame.

    ./harness/run.sh harness/clothes/trace_sleeve.py

The viewer's right arm hangs; its sleeve is the purple part of component 179
(split from the navy panel it shares a fill with by hue), and its cuff is 208.
The viewer's left arm is bent at the elbow, which this generator's straight arm
cannot do, so it is not traced: the one hanging sleeve is drawn on both arms,
mirrored, and a swung arm turns it with everything else below the sleeve hem.

A sleeve is placed along its arm rather than on the body, from the pivot at the
top of the arm to the wrist, so this records the reference's own two: the wrist
is the cuff's bottom centre, where the hand starts; the pivot is the sleeve's
centre line, fitted where it is visible below the hair, extended up to the height
`tall_chibi`'s arm pivots at. The hair hides the sleeve's top; its two edges are
carried up parallel to that centre line to just above the pivot, under the
jacket's shoulder.

Writes `out/clothes/sleeve.json` and `out/clothes/sleeve_overlay.png`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".claude/skills/trace-reference"))
import trace_lib as tl  # noqa: E402

from anime_character_creator import character as c  # noqa: E402

REF = Path(__file__).resolve().parents[3] / "time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OX, OY, SC = 650.0, 481.0, 173.7
OUT = Path("out/clothes")

rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
r, g = rgb[..., 0], rgb[..., 1]
lab, _ = ndi.label(rgb.sum(2) > 60)
disk = ndi.generate_binary_structure(2, 1)

sleeve = ndi.binary_opening((lab == 179) & (r > g + 3), disk, 2)
nl, _ = ndi.label(sleeve)
sizes = np.bincount(nl.ravel())
sizes[0] = 0
sleeve = nl == np.argmax(sizes)
cuff = ndi.binary_fill_holes(lab == 208)

# The centre line where the sleeve is fully visible (below the hair, above the cuff).
rows = [y for y in range(round(OY + 2.0 * SC), round(OY + 2.95 * SC)) if sleeve[y].any()]
mids = [(y, (np.nonzero(sleeve[y])[0].min() + np.nonzero(sleeve[y])[0].max()) / 2) for y in rows]
ys = np.array([m[0] for m in mids], float)
xs = np.array([m[1] for m in mids], float)
slope, intercept = np.polyfit(ys, xs, 1)

ref_body = c.skeleton_for(c.CharacterParams(body=c._GARMENT_REF_BODY))
_, top_y, _, _ = c._arm_line(ref_body)
pivot_y_hr = (top_y - ref_body.head_cy) / ref_body.head_r
pivot_row = OY + pivot_y_hr * SC
pivot = ((slope * pivot_row + intercept - OX) / SC, pivot_y_hr)
cy, cx = np.nonzero(cuff)
bottom = cy.max() - 2
brow = np.nonzero(cuff[bottom])[0]
wrist = (((brow.min() + brow.max()) / 2 - OX) / SC, (bottom - OY) / SC)

# Carry the edges up under the hair, parallel to the centre line.
first = rows[0]
lo0, hi0 = np.nonzero(sleeve[first])[0].min(), np.nonzero(sleeve[first])[0].max()
top_row = round(pivot_row - 0.08 * SC)
ext = sleeve.copy()
for y in range(top_row, first + 1):
    shift = slope * (y - first)
    ext[y, round(lo0 + shift) : round(hi0 + shift) + 1] = True
# Tuck the sleeve's bottom under the cuff so the two meet without a gap.
ext |= ndi.binary_dilation(cuff, disk, 2) & ndi.binary_dilation(ext, disk, 6)

result = {"pivot": pivot, "wrist": wrist}
over = Image.fromarray(np.clip(rgb * 3.0, 0, 255).astype("uint8"))
d = ImageDraw.Draw(over)
for name, m in (("sleeve", ext), ("cuff", cuff)):
    m = ndi.binary_fill_holes(ndi.binary_erosion(ndi.binary_dilation(m, disk, 3), disk, 3))
    m = ndi.binary_dilation(m, disk, 3)
    pts = [((x - OX) / SC, (y - OY) / SC) for x, y in tl.boundary(m)]
    start, segs = tl.fit_closed(pts, 0.010)
    result[name] = {"start": start, "segs": segs}
    d.line([(OX + x * SC, OY + y * SC) for x, y in tl.sample_chain(start, segs, 10)], fill="#00ff66", width=2)
    print(name, "segments", len(segs))
for pt, col in ((pivot, "#ff2255"), (wrist, "#33aaff")):
    px, py = OX + pt[0] * SC, OY + pt[1] * SC
    d.ellipse((px - 5, py - 5, px + 5, py + 5), outline=col, width=2)
print("pivot", pivot, "wrist", wrist, "centre-line slope", slope)
json.dump(result, open(OUT / "sleeve.json", "w"), indent=1)
over.crop((700, 700, 1000, 1110)).resize((600, 820)).save(OUT / "sleeve_overlay.png")
