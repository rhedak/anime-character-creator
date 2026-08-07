"""The traced silhouette against the one Satoko wears, both on our own head."""
import sys
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
from fit import fit_chain, marks
from satoko import locate, outer
from trace import on_ours, strip
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

C._hair_mass = lambda sk, p: ""
C._hair_front = lambda sk, p: ""
C._hair_defs = lambda sk, p: ""

at, _ = locate()
traced = fit_chain(outer(at), marks(outer(at), 0.055))
p = PRESETS["satoko"]
sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
current = C.HAIRSTYLES[p.hairstyle].mass(C._hair_fall(sk, p))
print(f"traced {len(traced[1])} segments; current {len(current[1])} segments")
strip(
    [on_ours([(current, (0, 150, 255)), (traced, (255, 0, 255))], "chibi", dash=0)],
    "out/trace/satoko_port.png",
)
