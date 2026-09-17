"""Write `out/clothes/collar.json` (from trace_cut.py) into COLLAR_CUTS["pointed"]."""

import json
from pathlib import Path

SRC = Path("src/anime_character_creator/character.py")
data = json.load(open("out/clothes/collar.json"))


def pt(p):
    return f"({p[0]:.3f}, {p[1]:.3f})"


def chain(c, pad):
    rows = [f"{pad}(", f"{pad}    {pt(c['start'])},", f"{pad}    ["]
    rows += [f"{pad}        ({pt(a)}, {pt(b)})," for a, b in c["segs"]]
    return rows + [f"{pad}    ],", f"{pad}),"]


s = SRC.read_text()
a = s.index('    "pointed": GarmentCut(')
b = s.index("\n}\n", a)
rows = ['    "pointed": GarmentCut(', "        fills=("]
for piece in ("back", "left", "right"):
    rows += chain(data[piece], " " * 12)
rows += ["        ),", "    ),"]
SRC.write_text(s[:a] + "\n".join(rows) + s[b:])
print("emitted")
