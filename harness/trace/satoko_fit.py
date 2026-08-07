import sys, math
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
from fit import fit_chain, marks
from satoko import inner, locate, outer
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS, build_skeleton

at, _ = locate()
for label, prof in (("mass", outer(at)), ("hairline", inner(at))):
    print(f"\n{label}: {len(prof)} bearings, "
          f"radius {min(r for _, r in prof):.3f}..{max(r for _, r in prof):.3f}")
    for tol in (0.020, 0.035, 0.055, 0.080):
        start, segs = fit_chain(prof, marks(prof, tol))
        anch = [start] + [e for _, e in segs]
        chords = [math.dist(anch[i], anch[i + 1]) for i in range(len(anch) - 1)]
        row = f"  tol {tol:.3f}  {len(segs):3d} segs  shortest {min(chords):.3f} r"
        for name in ("chibi", "realistic"):
            sk = build_skeleton(heads=BUILDS[name])
            per = [c * sk.head_r / C._stroke_w(sk) for c in chords]
            row += f"  | {name[:5]}: {sum(1 for q in per if q < 2)} under 2"
        print(row)
