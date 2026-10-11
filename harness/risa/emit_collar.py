"""Emit Risa's shirt collar as `character.py` source, before `def _arms(`
(`docs/risa-plan.md`, M5). Reads `out/risa/collar_trace.json`, which
`trace_collar.py` writes. Re-running replaces the previously emitted block.
"""

import json

SRC = "src/anime_character_creator/character.py"
BEGIN = "# Risa's shirt collar, per `docs/risa-plan.md` M5."
END = "# (end of the shirt collar)"
data = json.load(open("out/risa/collar_trace.json"))


def chain(c, indent):
    start, segs = c
    pad = " " * indent
    out = [f"{pad}({start[0]:.3f}, {start[1]:.3f}),", f"{pad}["]
    for (cx, cy), (ex, ey) in segs:
        out.append(f"{pad}    (({cx:.3f}, {cy:.3f}), ({ex:.3f}, {ey:.3f})),")
    out.append(f"{pad}],")
    return "\n".join(out)


# The shirt front between the wings' lower edges, under their crossing: in her reference
# it is shirt up to the collar, and ours draws the tunic only from the shoulder line, so a
# patch of the neck's skin showed round the ribbon's knot. A polygon on those edges
# (pixels on her composite, from `collar_trace.json`), drawn under the wings.
R, CHIN = 140.25, 399
CY = CHIN - 1.02 * R
FRONT_PX = [(629, 435), (645, 442), (660, 466), (601, 466), (613, 447)]
front_pts = [((x - data["axis_x"]) / R, (y - CY) / R) for x, y in FRONT_PX]
front = (
    front_pts[0],
    [
        (((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b)
        for a, b in zip(front_pts, front_pts[1:] + front_pts[:1])
    ],
)

lines = [
    BEGIN,
    "# Traced by `harness/risa/trace_collar.py` off `segments/white-collared-shirt.png`: the",
    "# two wings as one outline, touching at the foot of their V where the ribbon's knot sits",
    "# and open above it, so her neck shows between them. An open collar, unlike the closed",
    "# band `_collar` draws without a cut. Head radii on `tall_slender`, x from the collar's",
    "# own centre line.",
    'COLLAR_CUTS["shirt"] = GarmentCut(',
    "    fills=(",
    "        # the shirt front under the crossing",
    "        (",
    chain(front, 12),
    "        ),",
    "        # the wings",
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
