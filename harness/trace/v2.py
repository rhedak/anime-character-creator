import sys
sys.path.insert(0, "out/trace")
from fit import fit_chain, marks, profile
from trace import on_ref, strip

prof = profile()
for prom in (0.030, 0.055, 0.085):
    mk = marks(prof, prom)
    ch = fit_chain(prof, mk)
    print(f"prominence {prom}: {len(mk)} marks, {len(ch[1])} segments")
    strip([on_ref([(ch, (255, 0, 255))], dash=0)], f"out/trace/v2_{int(prom*1000)}.png")
