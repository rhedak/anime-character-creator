"""Emit Mio's blazer as `character.py` source, before `def _arms(`
(`docs/mio-plan.md`, M7). Reads `out/mio/blazer_trace.json`, which `trace_blazer.py`
writes. Re-running replaces the previously emitted block.

Three things come out: the blazer itself (`COAT_CUTS["blazer"]`), the pocket flap
(`HIP_POCKET_CUT`, both sides, the traced right one mirrored for the left) and the
button positions (`_COAT_BUTTONS`).
"""

import json

SRC = "src/anime_character_creator/character.py"
BEGIN = "# Mio's blazer, per `docs/mio-plan.md` M7."
END = "# (end of the blazer)"
data = json.load(open("out/mio/blazer_trace.json"))


def chain(c, indent):
    start, segs = c
    pad = " " * indent
    out = [f"{pad}({start[0]:.3f}, {start[1]:.3f}),", f"{pad}["]
    for (cx, cy), (ex, ey) in segs:
        out.append(f"{pad}    (({cx:.3f}, {cy:.3f}), ({ex:.3f}, {ey:.3f})),")
    out.append(f"{pad}],")
    return "\n".join(out)


def tup(c, indent, note=None):
    pad = " " * indent
    head = [f"{pad}# {note}"] if note else []
    return "\n".join([*head, f"{pad}(", chain(c, indent + 4), f"{pad}),"])


def mirror(c):
    (sx, sy), segs = c
    return ((-sx, sy), [((-cx, cy), (-ex, ey)) for (cx, cy), (ex, ey) in segs])


lines = [
    BEGIN,
    "# Traced by `harness/mio/trace_blazer.py` off `segments/school-blazer.png`: the whole",
    "# garment as one silhouette, sleeves included (the reference draws it as one fill, and",
    "# her hair hides the shoulders, so the strips beside the torso are filled), the two",
    "# lapel facings with their notches over it, and the line work: the front line from the",
    "# lapels' point to the hem and the two side lines where the torso passes in front of the",
    "# sleeve. The neck opening is the shirt's V. Head radii on `tall_slender`, x from the",
    "# blazer's own centre line. Pockets and buttons are parts of their own.",
    'COAT_CUTS["blazer"] = GarmentCut(',
    "    fills=(",
    tup(data["silhouette"], 8, "the garment"),
    tup(data["lapels"][0], 8, "the left lapel"),
    tup(data["lapels"][1], 8, "the right lapel"),
    "    ),",
    "    lines=(",
]
for name, c in zip(("front line", "left side line", "right side line"), data["lines"]):
    lines.append(tup(c, 8, name))
lines += [
    "    ),",
    '    ref_body="tall_slender",',
    "    line_weight=1.0,",
    ")",
    "",
    "# A flapped hip pocket, one flap a side: the right one traced, the left its mirror.",
    "HIP_POCKET_CUT = GarmentCut(",
    "    fills=(",
    tup(data["pocket"], 8, "right"),
    tup(mirror(data["pocket"]), 8, "left"),
    "    ),",
    '    ref_body="tall_slender",',
    ")",
    "",
    "# The blazer's buttons, as (x, y, radius) in head radii on `tall_slender`, x from the",
    "# blazer's centre line: a line of three down the front.",
    "_COAT_BUTTONS: tuple[tuple[float, float, float], ...] = (",
]
for b in data["buttons"]:
    lines.append(f"    ({b['x']:.3f}, {b['y']:.3f}, {b['r']:.3f}),")
lines += [")", END]
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
print(
    "emitted",
    sum(len(c[1]) for c in [data["silhouette"], *data["lapels"], *data["lines"], data["pocket"]]),
    "segments",
)
