"""Does the finest traced detail survive our own line weight and output size?

A tooth narrower than about twice the stroke closes up into a black wedge rather
than reading as two locks, which is the failure task 73 hit on the fringe. This
measures the traced chain's own feature sizes against `_stroke_w` at both builds
and at both the working canvas and the 2x `ref-out` size.
"""
import math, sys
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
from fit import fit_chain, marks, profile
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS, build_skeleton

prof = profile()
for tol in (0.018, 0.030, 0.045, 0.065, 0.090):
    mk = marks(prof, tol)
    start, segs = fit_chain(prof, mk)
    pts = [start] + [e for _, e in segs]
    chords = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    smallest = min(chords)
    median = sorted(chords)[len(chords) // 2]
    row = f"tol {tol:.3f} {len(segs):3d} segs  shortest {smallest:.3f} r  median {median:.3f} r"
    for name in ("chibi", "realistic"):
        sk = build_skeleton(heads=BUILDS[name])
        sw = C._stroke_w(sk)
        # ref-out renders at 2x the working canvas, so the ratio is scale-free.
        per_stroke = [c * sk.head_r / sw for c in chords]
        under = sum(1 for v in per_stroke if v < 2.0)
        row += f"  | {name[:5]}: min {min(per_stroke):.1f} strokes, {under} edges under 2"
    print(row)

sk = build_skeleton(heads=BUILDS["chibi"])
print(f"\nchibi: head radius {sk.head_r:.0f}px on the 400x500 canvas, stroke {C._stroke_w(sk):.2f}px")
sk = build_skeleton(heads=BUILDS["realistic"])
print(f"adult: head radius {sk.head_r:.0f}px, stroke {C._stroke_w(sk):.2f}px")
