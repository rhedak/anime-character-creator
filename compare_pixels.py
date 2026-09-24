#!/usr/bin/env python3
"""Pixel-exact PNG comparison for refresh-ref-out.sh --pixels.

refresh-ref-out.sh's default and --check modes decide staleness by SVG bytes
(see that script's own comment on why: the SVG is deterministic text, where a
PNG can differ in bytes for reasons that are not the drawing). That is exactly
right for "did the drawing change" but wrong for a narrower question this
exists to answer: does a change that only touches the SVG source, a new layer,
reordered elements, added markup, actually move a single visible pixel? SVG
bytes always differ then, so the byte comparison alone would report every
preset as changed even when nothing painted differently. Only a decoded-pixel
comparison can tell you nothing moved.

Usage:
    compare_pixels.py <stage_dir> <ref_out_dir> <rel1.png> [rel2.png ...]

Each relN.png is a path relative to both stage_dir and ref_out_dir, exactly as
refresh-ref-out.sh already tracks them (e.g. "satoko.png",
"on-white/satoko.png", "real/satoko.png", "cover.png"). Prints one line per
file that differs, giving the changed pixel count and the bounding box of the
changed pixels, then a summary line. Exits 1 if any file differs, 0 if every
file matches exactly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


def compare_one(staged: Path, committed: Path) -> tuple[int, tuple[int, int, int, int] | None]:
    """Return (changed pixel count, bounding box) for one PNG pair.

    The box is (x0, y0, x1, y1) with x1/y1 exclusive, i.e. a slice you could
    hand back to PIL's crop(), and is None when nothing changed. A size
    mismatch is reported as the whole staged image having changed rather than
    attempted as a numpy comparison, which would just refuse to broadcast.
    """
    a = np.asarray(Image.open(staged).convert("RGBA"))
    b = np.asarray(Image.open(committed).convert("RGBA"))
    if a.shape != b.shape:
        h, w = a.shape[:2]
        return h * w, (0, 0, w, h)
    diff = np.any(a != b, axis=-1)
    count = int(diff.sum())
    if count == 0:
        return 0, None
    ys, xs = np.nonzero(diff)
    return count, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print("usage: compare_pixels.py <stage_dir> <ref_out_dir> <rel.png>...", file=sys.stderr)
        return 2
    stage_dir = Path(argv[1])
    ref_out_dir = Path(argv[2])
    rels = argv[3:]

    differing = 0
    for rel in rels:
        staged = stage_dir / rel
        committed = ref_out_dir / rel
        if not committed.exists():
            print(f"  PIXELS     {rel}  (no committed file to compare)")
            differing += 1
            continue
        count, box = compare_one(staged, committed)
        if count:
            x0, y0, x1, y1 = box
            print(f"  PIXELS     {rel}  {count} px changed, bbox=({x0}, {y0}, {x1}, {y1})")
            differing += 1

    print(f"{differing} of {len(rels)} PNGs differ in pixels")
    return 1 if differing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
