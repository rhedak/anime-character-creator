"""Emit the fitted fringe, and the notches, as Python literals."""
import sys
sys.path.insert(0, "out/trace")
from fringe import fit, profile, simplify

import sys as _s
BLUNT = float(_s.argv[1]) if len(_s.argv) > 1 else 1.0
raw = [(u, v) for u, v in profile()]
mid = sum(v for _, v in raw) / len(raw)
pts = [(u, mid + (v - mid) * BLUNT) for u, v in raw]
start, segs = fit(pts, simplify(pts, 0.035))
print(f"# {len(segs)} segments")
print(f"_CROP_FRINGE_START: Point = ({start[0]:.3f}, {start[1]:.3f})")
print("_CROP_FRINGE: list[Segment] = [")
for (cx, cy), (ex, ey) in segs:
    print(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
print("]")

# notches: anchors that are higher than both neighbours, i.e. where two locks meet
anchors = [start] + [e for _, e in segs]
notches = [
    anchors[i]
    for i in range(1, len(anchors) - 1)
    if anchors[i][1] < anchors[i - 1][1] and anchors[i][1] < anchors[i + 1][1]
]
print("_CROP_NOTCHES: list[Point] = [")
for x, y in notches:
    print(f"    ({x:6.3f}, {y:6.3f}),")
print("]")
tips = [a for a in anchors if a[1] > -0.15]
print(f"# {len(notches)} notches, {len(tips)} anchors below y=-0.15")
print(f"# fringe spans x {anchors[0][0]:+.2f}..{anchors[-1][0]:+.2f}, y {min(a[1] for a in anchors):+.3f}..{max(a[1] for a in anchors):+.3f}")
