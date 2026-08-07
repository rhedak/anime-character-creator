import sys, math
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
from fringe import fit, simplify
from fringe3 import locate, profile
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS, build_skeleton

at, _, _ = locate()
pts = profile(at)
print(f"{len(pts)} columns from the crop")
for tol in (0.045, 0.060, 0.080):
    keep = simplify(pts, tol)
    start, segs = fit(pts, keep)
    anch = [start] + [e for _, e in segs]
    chords = [math.dist(anch[i], anch[i + 1]) for i in range(len(anch) - 1)]
    tips = [i for i in range(1, len(anch) - 1)
            if anch[i][1] > anch[i - 1][1] and anch[i][1] > anch[i + 1][1]]
    row = f"tol {tol:.3f}  {len(segs):3d} segs  {len(tips):2d} tips  shortest {min(chords):.3f} r"
    for name in ("chibi", "realistic"):
        sk = build_skeleton(heads=BUILDS[name])
        per = [c * sk.head_r / C._stroke_w(sk) for c in chords]
        row += f"  | {name[:5]}: min {min(per):.1f} strokes, {sum(1 for q in per if q < 2)} under 2"
    print(row)
