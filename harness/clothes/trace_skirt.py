"""Trace the dress's skirt off katherina_grok.jpg, carried under what hides it.

    ./harness/run.sh harness/clothes/trace_skirt.py

The skirt (component 204) shows in two places: a narrow strip between the
jacket's lower panels, and the whole flared width below the jacket's hem. The
belt covers its top and the jacket's panels its sides above 3.22 head radii.
The traced shape is the visible fill, unioned with a continuation under those:
edges from the belt's own width at the waist (±0.58 at 2.36, where the skirt
starts) straight to the first fully visible row below the jacket (measured,
per side), the same measure-both-ends-and-interpolate the staff's shaft got
behind the fist. The jacket drawn over it covers exactly that continuation.

Writes `out/clothes/skirt.json` and `out/clothes/skirt_overlay.png`.
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

REF = Path(__file__).resolve().parents[3] / "time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OX, OY, SC = 650.0, 481.0, 173.7
OUT = Path("out/clothes")

rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
lab, _ = ndi.label(rgb.sum(2) > 60)
disk = ndi.generate_binary_structure(2, 1)
skirt = lab == 204

TOP_Y = 2.36
BELT_HALF = 0.58
top_row = round(OY + TOP_Y * SC)
# First row below the jacket's hem where the skirt spans its full width.
full_row = round(OY + 3.24 * SC)
xs = np.nonzero(skirt[full_row])[0]
left_full, right_full = xs.min(), xs.max()
mask = skirt.copy()
for row in range(top_row, full_row + 1):
    t = (row - top_row) / (full_row - top_row)
    lo = (1 - t) * (OX - BELT_HALF * SC) + t * left_full
    hi = (1 - t) * (OX + BELT_HALF * SC) + t * right_full
    mask[row, round(lo) : round(hi) + 1] = True
mask = ndi.binary_fill_holes(ndi.binary_erosion(ndi.binary_dilation(mask, disk, 3), disk, 3))
mask = ndi.binary_dilation(mask, disk, 3)  # to the outline's centre line
mask[: top_row, :] = False

pts = [((x - OX) / SC, (y - OY) / SC) for x, y in tl.boundary(mask)]
start, segs = tl.fit_closed(pts, 0.010)
print("skirt raw", len(pts), "segments", len(segs), "full row edges", (left_full - OX) / SC, (right_full - OX) / SC)
OUT.mkdir(parents=True, exist_ok=True)
json.dump({"skirt": {"start": start, "segs": segs}}, open(OUT / "skirt.json", "w"), indent=1)
over = Image.fromarray(np.clip(rgb * 2.5, 0, 255).astype("uint8"))
d = ImageDraw.Draw(over)
d.line([(OX + x * SC, OY + y * SC) for x, y in tl.sample_chain(start, segs, 10)], fill="#00ff66", width=2)
over.crop((380, 840, 920, 1260)).save(OUT / "skirt_overlay.png")
print("median colour", "#%02x%02x%02x" % tuple(np.median(rgb[ndi.binary_erosion(skirt, iterations=3)], axis=0).astype(int)))
