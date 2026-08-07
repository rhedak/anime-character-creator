import sys
sys.path.insert(0, "out/trace")
from fit import fit_chain, marks, profile
from trace import on_ref, strip

prof = profile()
for tol in (0.065, 0.090, 0.120):
    mk = marks(prof, tol)
    ch = fit_chain(prof, mk)
    print(f"tol {tol}: {len(mk)} marks, {len(ch[1])} segments")
    strip([on_ref([(ch, (255, 0, 255))], dash=0)], f"out/trace/v3_{int(tol*1000)}.png")
