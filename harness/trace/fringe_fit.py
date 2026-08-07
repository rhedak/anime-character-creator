import sys
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
from fringe import fit, profile, simplify
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS, build_skeleton
import math

pts = [(u, v) for u, v in profile()]
print(f"{len(pts)} measured columns")
for tol in (0.010, 0.020, 0.035, 0.050):
    keep = simplify(pts, tol)
    start, segs = fit(pts, keep)
    anchors = [start] + [e for _, e in segs]
    chords = [math.dist(anchors[i], anchors[i + 1]) for i in range(len(anchors) - 1)]
    row = f"tol {tol:.3f}  {len(segs):3d} segs  shortest {min(chords):.3f} r"
    for name in ("chibi", "realistic"):
        sk = build_skeleton(heads=BUILDS[name])
        per = [c * sk.head_r / C._stroke_w(sk) for c in chords]
        row += f"  | {name[:5]}: min {min(per):.1f} strokes, {sum(1 for v in per if v < 2)} under 2"
    print(row)
