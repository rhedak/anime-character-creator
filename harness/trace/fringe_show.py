import sys
sys.path.insert(0, "out/trace")
from fringe import fit, profile, simplify
from trace import on_ref, strip

pts = [(u, v) for u, v in profile()]
chains = []
for tol, col in ((0.100, (255, 0, 255)),):
    start, segs = fit(pts, simplify(pts, tol))
    chains.append(((start, segs), col))
    print(f"tol {tol}: {len(segs)} segments, start {start}")
strip([on_ref(chains, box=(300, 60, 590, 260), zoom=4, dash=0)], "out/trace/fringe_fit.png")
