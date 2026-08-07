import sys, math
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
from fit import fit_chain, marks
from fringe import fit as fit_xy, simplify
from satoko import hairline, locate, outer
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS, build_skeleton

at, _ = locate()
start, segs = fit_chain(outer(at), marks(outer(at), 0.035))
print(f"_LONG_EDGE_START: Point = ({start[0]:.3f}, {start[1]:.3f})")
print("_LONG_EDGE: list[Segment] = [")
for (cx, cy), (ex, ey) in segs:
    print(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
print("]")
print(f"# mass {len(segs)} segments")

pts = hairline(at)
for tol in (0.010, 0.018, 0.030):
    keep = simplify(pts, tol)
    hs, hg = fit_xy(pts, keep)
    anch = [hs] + [e for _, e in hg]
    chords = [math.dist(anch[i], anch[i + 1]) for i in range(len(anch) - 1)]
    bad = []
    for name in ("chibi", "realistic"):
        sk = build_skeleton(heads=BUILDS[name])
        per = [c * sk.head_r / C._stroke_w(sk) for c in chords]
        bad.append(sum(1 for q in per if q < 2))
    print(f"# hairline tol {tol}: {len(hg)} segs, under 2 strokes {bad}", file=sys.stderr)

keep = simplify(pts, 0.030)
hs, hg = fit_xy(pts, keep)
print(f"_LONG_LINE_START: Point = ({hs[0]:.3f}, {hs[1]:.3f})")
print("_LONG_LINE: list[Segment] = [")
for (cx, cy), (ex, ey) in hg:
    print(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
print("]")
print(f"# hairline {len(hg)} segments")
