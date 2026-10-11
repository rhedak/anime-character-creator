"""Emit Mio's ribbon as `character.py` source, before `def _arms(`
(`docs/mio-plan.md`, M6). Reads `out/mio/ribbon_trace.json`, which
`trace_ribbon.py` writes. Re-running replaces the previously emitted block.
"""

import json

SRC = "src/anime_character_creator/character.py"
BEGIN = "# Mio's ribbon, per `docs/mio-plan.md` M6."
END = "# (end of the ribbon)"
data = json.load(open("out/mio/ribbon_trace.json"))
NAMES = ["left tail", "right tail", "left loop", "right loop", "knot"]


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
    "# Traced by `harness/mio/trace_ribbon.py` off `segments/blue-ribbon.png` as five",
    "# overlapping pieces drawn in the order they are tied, the tails, then the loops over",
    "# their tops, then the knot over both, so that their outlines are the fold lines and",
    "# none has to be traced as interior line work. Each loop has a slit cut out of it, with",
    "# the shirt showing through. Head radii on `tall_slender`, x from the collar's own",
    "# centre line.",
    "RIBBON_CUT = GarmentCut(",
    "    fills=(",
]
for name, c in zip(NAMES, data["fills"]):
    lines.append(f"        # {name}")
    lines.append("        (")
    lines.append(chain(c, 12))
    lines.append("        ),")
lines += ["    ),", "    holes=("]
for idx, c in data["holes"]:
    lines.append(f"        # a slit in the {NAMES[idx]}")
    lines.append(f"        ({idx}, (")
    lines.append(chain(c, 12))
    lines.append("        )),")
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
print("emitted", sum(len(c[1]) for c in data["fills"]) + sum(len(c[1]) for _, c in data["holes"]), "segments")
