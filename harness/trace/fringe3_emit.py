import sys
sys.path.insert(0, "out/trace")
from fringe import fit, simplify
from fringe3 import locate, profile

at, _, _ = locate()
pts = profile(at)
start, segs = fit(pts, simplify(pts, 0.045))
print(f"# {len(segs)} segments, traced off ref/satoshi-chibi-fringe.png")
print(f"_CROP_FRINGE_START: Point = ({start[0]:.3f}, {start[1]:.3f})")
print("_CROP_FRINGE: list[Segment] = [")
for (cx, cy), (ex, ey) in segs:
    print(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
print("]")
anch = [start] + [e for _, e in segs]
notches = [anch[i] for i in range(1, len(anch) - 1)
           if anch[i][1] < anch[i - 1][1] and anch[i][1] < anch[i + 1][1]]
print("_CROP_NOTCHES: list[Point] = [")
for x, y in notches:
    print(f"    ({x:6.3f}, {y:6.3f}),")
print("]")
print(f"# {len(notches)} notches; spans x {anch[0][0]:+.2f}..{anch[-1][0]:+.2f},"
      f" y {min(a[1] for a in anch):+.3f}..{max(a[1] for a in anch):+.3f}")
