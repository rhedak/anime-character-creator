import sys
sys.path.insert(0, "out/trace")
from fit import marks, profile, polar

prof = profile()
mk = marks(prof, 0.055)
print(f"{len(mk)} marks (bearing, radius), 0 = straight up, + = character's left\n")
prev = None
for d, r in mk:
    kind = ""
    if prev is not None:
        kind = "tip " if r > prev else "notch"
    print(f"  ({d:6.0f}, {r:.3f})   {kind}   y={polar(d, r)[1]:+.3f}  x={polar(d, r)[0]:+.3f}")
    prev = r
top = min(polar(d, r)[1] for d, r in mk)
wide = max(abs(polar(d, r)[0]) for d, r in mk)
print(f"\ntopmost mark y={top:+.3f} head radii (ceiling is -1.36 including stroke)")
print(f"widest mark  x={wide:.3f} head radii")
