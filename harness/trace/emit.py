"""Emit the fitted chain as Python literals to paste into character.py."""
import sys
sys.path.insert(0, "out/trace")
from fit import fit_chain, marks, profile

prof = profile()
start, segs = fit_chain(prof, marks(prof, 0.065))
print(f"# {len(segs)} segments")
print(f"_CROP_START: Point = ({start[0]:.3f}, {start[1]:.3f})")
print("_CROP_EDGE: list[Segment] = [")
for (cx, cy), (ex, ey) in segs:
    print(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
print("]")
lows = [start[1]] + [e[1] for _, e in segs]
print(f"# lowest end y {max(lows):.3f}   highest {min(lows):.3f}")
