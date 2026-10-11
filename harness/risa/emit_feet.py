"""Emit Risa's knee sock and loafer as `character.py` source, before `def _arms(`
(`docs/risa-plan.md`, M3). Reads `out/risa/feet_trace.json`, which `trace_feet.py`
writes. Re-running replaces the previously emitted block.

Coordinates are cut coordinates for a `per_leg` cut: head radii on `tall_slender`,
the right leg's, with x from the leg's own centre line.
"""

import json

SRC = "src/anime_character_creator/character.py"
BEGIN = "# Risa's knee sock and loafer, per `docs/risa-plan.md` M3."
END = "# (end of the feet)"
data = json.load(open("out/risa/feet_trace.json"))
# The sole's tone against the loafer's own, as `shade()`'s value factor: the
# reference's sole #332921 over its leather #433228 is 0.76 in value, and `shade`
# adds a little saturation on top, so a touch above.
SOLE_SHADE = 0.78


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


lines = [BEGIN]
lines += [
    "# Traced by `harness/risa/trace_feet.py` off `segments/anime-girl.png` (the sock, the",
    "# one component of the leg colour below the skirt, grown to the stroke's centre line",
    "# and run on down under the shoe) and `segments/brown-loafers/` (the silhouette, the",
    "# saddle seam, the slit, the toe cap and the sole line, and the sole band as a second",
    "# tone). The right leg, in head radii on `tall_slender`, x from the leg's centre line:",
    "# `per_leg` mirrors it for the left. The reference's own sock and shoe are one pair",
    "# that are not quite mirror images of each other; one is traced and mirrored.",
    "KNEE_SOCK_CUT = GarmentCut(",
    "    fills=(",
    tup(data["sock"], 8),
    "    ),",
    '    ref_body="tall_slender",',
    "    per_leg=True,",
    ")",
    "BOOT_CUTS: dict[str, GarmentCut] = {",
    '    "loafer": GarmentCut(',
    "        fills=(",
    tup(data["loafer"], 12),
]
if data.get("loafer_sole"):
    lines.append(tup(data["loafer_sole"], 12))
lines += ["        ),", "        lines=("]
for ln in data["loafer_lines"]:
    lines.append(tup(ln, 12))
lines += [
    "        ),",
    f"        shades=(None, {SOLE_SHADE}),",
    '        ref_body="tall_slender",',
    "        per_leg=True,",
    "    ),",
    "}",
    END,
]
block = "\n".join(lines) + "\n\n\n"

src = open(SRC).read()
if BEGIN in src:
    a = src.index(BEGIN)
    b = src.index(END, a) + len(END)
    src = src[:a] + block.rstrip("\n") + src[b:]
else:
    marker = "def _arms("
    i = src.index(marker)
    src = src[:i] + block + src[i:]
open(SRC, "w").write(src)
print(
    "emitted",
    sum(len(c[1]) for c in [data["sock"], data["loafer"], *data["loafer_lines"]]),
    "segments",
)
