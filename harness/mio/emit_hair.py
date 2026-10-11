"""Emit Mio's hair as `character.py` source, before `class Hairstyle`
(`docs/mio-plan.md`, M8). Reads `out/mio/hair_trace.json`, which `trace_hair.py` writes.
Re-running replaces the previously emitted block.
"""

import json

SRC = "src/anime_character_creator/character.py"
BEGIN = "# BEGIN fringed trace"
END = "# END fringed trace"
data = json.load(open("out/mio/hair_trace.json"))


def chain(c, indent):
    start, segs = c
    pad = " " * indent
    out = [f"{pad}({start[0]:.3f}, {start[1]:.3f}),", f"{pad}["]
    for (cx, cy), (ex, ey) in segs:
        out.append(f"{pad}    (({cx:.3f}, {cy:.3f}), ({ex:.3f}, {ey:.3f})),")
    out.append(f"{pad}],")
    return "\n".join(out)


def one(name, c, doc):
    return [*[f"# {line}" for line in doc], f"{name}: Chain = (", chain(c, 4), ")"]


def many(name, cs, doc):
    out = [*[f"# {line}" for line in doc], f"{name}: list[Chain] = ["]
    for c in cs:
        out += ["    (", chain(c, 8), "    ),"]
    return [*out, "]"]


tip = max(max(e[1] for _, e in data["front"][1]), data["front"][0][1])
lines = [
    BEGIN,
    "# Traced by `harness/mio/trace_hair.py` off `segments/long-black-hair.png` and",
    "# `segments/bangs.png` (`docs/mio-plan.md`, M8). Head radii on the figure's own head, x",
    "# from its centre line, so a cut is the same hair on any body; `_fringed_q` stretches",
    "# the part below the cheek line to `hair_length`.",
    f"_FRINGED_BASE_TIP = {tip:.3f}",
    *one(
        "_FRINGED_FRONT",
        data["front"],
        [
            "The hair in front: the fringe, the face opening and the two long curtains of locks as",
            "one closed outline, the stroke's centre line.",
        ],
    ),
    *one(
        "_FRINGED_MASS",
        data["mass"],
        [
            "The silhouette behind the body: the same outline with the gap between the curtains",
            "closed across, below the chin, where the blazer hides it.",
        ],
    ),
    *many(
        "_FRINGED_STRANDS",
        data["strands"],
        ["The strokes that part the hair into locks, open chains."],
    ),
    *many(
        "_FRINGED_OPENINGS",
        data["openings"],
        ["The patches of skin showing through the hair: an ear at each side and a gap in the fringe."],
    ),
    *many(
        "_FRINGED_SHADE",
        data["shade"],
        ["The darker hair behind, where it shows in front: regions painted in the second tone."],
    ),
    END,
]
block = "\n".join(lines) + "\n\n\n"
src = open(SRC).read()
if BEGIN in src:
    a = src.index(BEGIN)
    b = src.index(END, a) + len(END)
    src = src[:a] + block.rstrip("\n") + src[b:]
else:
    i = src.index("@dataclass(frozen=True)\nclass Hairstyle:")
    src = src[:i] + block + src[i:]
open(SRC, "w").write(src)
print(
    "emitted front",
    len(data["front"][1]),
    "mass",
    len(data["mass"][1]),
    "strands",
    len(data["strands"]),
    "tip",
    round(tip, 3),
)
