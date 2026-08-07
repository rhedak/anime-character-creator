"""Port check: the traced silhouette laid on our own head, at both builds."""
import sys
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
from fit import fit_chain, marks, profile
from trace import on_ours, on_ref, strip
from anime_character_creator import character as C

C._hair_mass = lambda sk, p: ""
C._hair_front = lambda sk, p: ""
C._hair_defs = lambda sk, p: ""

prof = profile()
mk = marks(prof, 0.090)
ch = fit_chain(prof, mk)
print(f"{len(ch[1])} segments")
strip(
    [
        on_ref([(ch, (255, 0, 255))], dash=0),
        on_ours([(ch, (255, 0, 255))], "realistic", dash=0),
        on_ours([(ch, (255, 0, 255))], "chibi", dash=0),
    ],
    "out/trace/v4.png",
)
