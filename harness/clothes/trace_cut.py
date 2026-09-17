"""Trace garment pieces off katherina_grok.jpg as fill components, in head radii.

    ./harness/run.sh harness/clothes/trace_cut.py <name> <tol> <piece>=<id>[+<id>...] ...

Each piece is the union of the listed reference fill components (ids from
`scipy.ndimage.label(rgb.sum(2) > 60)`, as `harness/body/landmarks.py` lists
them), closed across the outlines between them, grown by half the reference's
outline width so its boundary is the stroke's centre line, walked and fitted
exactly as the witch hat was. Coordinates are the reference's own head radii,
which are `tall_chibi`'s, the body cuts are mapped from.

Writes `out/clothes/<name>.json` (pieces in the order given, which is the
drawing order) and `out/clothes/<name>_overlay.png`.
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
HALF_STROKE = 3
OUT = Path("out/clothes")


def main() -> None:
    name, tol = sys.argv[1], float(sys.argv[2])
    pieces = []
    for arg in sys.argv[3:]:
        piece, ids = arg.split("=")
        pieces.append((piece, [int(i) for i in ids.split("+")]))

    rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
    lab, _ = ndi.label(rgb.sum(2) > 60)
    disk = ndi.generate_binary_structure(2, 1)

    over = Image.fromarray(np.clip(rgb * 2.5, 0, 255).astype("uint8"))
    d = ImageDraw.Draw(over)
    colours = ["#00ff66", "#ff3355", "#33aaff", "#ffee00", "#ff00ff", "#00ffff"]
    result = {}
    box = None
    for (piece, ids), col in zip(pieces, colours * 4, strict=False):
        m = np.isin(lab, ids)
        m = ndi.binary_dilation(m, structure=disk, iterations=3)
        m = ndi.binary_fill_holes(ndi.binary_erosion(m, structure=disk, iterations=3))
        m = ndi.binary_dilation(m, structure=disk, iterations=HALF_STROKE)
        pts = [((x - OX) / SC, (y - OY) / SC) for x, y in tl.boundary(m)]
        start, segs = tl.fit_closed(pts, tol)
        result[piece] = {"start": start, "segs": segs, "ids": ids}
        poly = tl.sample_chain(start, segs, 10)
        d.line([(OX + x * SC, OY + y * SC) for x, y in poly], fill=col, width=1)
        ys, xs = np.nonzero(m)
        b = (xs.min(), ys.min(), xs.max(), ys.max())
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        print(piece, "raw", len(pts), "segments", len(segs))
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(OUT / f"{name}.json", "w"), indent=1)
    pad = 20
    crop = over.crop((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad))
    zoom = max(1, round(600 / max(crop.size)))
    crop.resize((crop.width * zoom, crop.height * zoom)).save(OUT / f"{name}_overlay.png")


if __name__ == "__main__":
    main()
