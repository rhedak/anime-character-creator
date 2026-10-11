"""Emit Mio's shirt collar as `character.py` source, before `def _arms(`
(`docs/mio-plan.md`, M5). Reads `out/mio/collar_trace.json`, which
`trace_collar.py` writes. Re-running replaces the previously emitted block.
"""

import json

SRC = "src/anime_character_creator/character.py"
BEGIN = "# Mio's shirt collar, per `docs/mio-plan.md` M5."
END = "# (end of the shirt collar)"
data = json.load(open("out/mio/collar_trace.json"))


def chain(c, indent):
    start, segs = c
    pad = " " * indent
    out = [f"{pad}({start[0]:.3f}, {start[1]:.3f}),", f"{pad}["]
    for (cx, cy), (ex, ey) in segs:
        out.append(f"{pad}    (({cx:.3f}, {cy:.3f}), ({ex:.3f}, {ey:.3f})),")
    out.append(f"{pad}],")
    return "\n".join(out)


lines = [
    BEGIN,
    "# Traced by `harness/mio/trace_collar.py` off `segments/white-collared-shirt.png`: the",
    "# two wings as one outline, touching at the foot of their V where the ribbon's knot sits",
    "# and open above it, so her neck shows between them. An open collar, unlike the closed",
    "# band `_collar` draws without a cut. Head radii on `tall_slender`, x from the collar's",
    "# own centre line.",
    'COLLAR_CUTS["shirt"] = GarmentCut(',
    "    fills=(",
    "        (",
    chain(data["collar"], 12),
    "        ),",
    "    ),",
    '    ref_body="tall_slender",',
    ")",
    END,
]
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
print("emitted", len(data["collar"][1]), "segments")
