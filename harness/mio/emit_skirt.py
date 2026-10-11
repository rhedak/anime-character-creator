"""Emit Mio's pleated skirt as `character.py` source, before `def _arms(`
(`docs/mio-plan.md`, M4). Reads `out/mio/skirt_trace.json`, which `trace_skirt.py`
writes. Re-running replaces the previously emitted block.
"""

import json

SRC = "src/anime_character_creator/character.py"
BEGIN = "# Mio's pleated skirt, per `docs/mio-plan.md` M4."
END = "# (end of the pleated skirt)"
data = json.load(open("out/mio/skirt_trace.json"))


def chain(c, indent):
    start, segs = c
    pad = " " * indent
    out = [f"{pad}({start[0]:.3f}, {start[1]:.3f}),", f"{pad}["]
    for (cx, cy), (ex, ey) in segs:
        out.append(f"{pad}    (({cx:.3f}, {cy:.3f}), ({ex:.3f}, {ey:.3f})),")
    out.append(f"{pad}],")
    return "\n".join(out)


def tup(c, indent):
    pad = " " * indent
    return f"{pad}(\n{chain(c, indent + 4)}\n{pad}),"


lines = [
    BEGIN,
    "# Traced by `harness/mio/trace_skirt.py` off `segments/pleated-skirt.png`: the",
    "# silhouette with its stepped hem, carried up behind the blazer along its own side",
    "# slopes (the reference's top edge is the blazer's hem), and the six fold lines",
    "# between the seven pleat faces as open strokes. Folds are line work and not tone:",
    "# the reference's alternating skirt tones are a shading plane across a garment,",
    "# which `CLAUDE.md` rules out. Head radii on `tall_slender`, x from the silhouette's",
    "# own centre line.",
    'SKIRT_CUTS["pleated"] = GarmentCut(',
    "    fills=(",
    tup(data["silhouette"], 8),
    "    ),",
    "    lines=(",
]
for c in data["folds"]:
    lines.append(tup(c, 8))
lines += ["    ),", '    ref_body="tall_slender",', ")", END]
block = "\n".join(lines) + "\n\n\n"

src = open(SRC).read()
if BEGIN in src:
    a = src.index(BEGIN)
    b = src.index(END, a) + len(END)
    src = src[:a] + block.rstrip("\n") + src[b:]
else:
    i = src.index("def _arms(")
    src = src[:i] + block + src[i:]
open(SRC, "w").write(src)
print("emitted", len(data["silhouette"][1]) + sum(len(c[1]) for c in data["folds"]), "segments")
