"""Write `out/clothes/shoulders.json` into character.py: the open jacket's two
pieces and the wide sleeve (its joint and shape). Rerun after trace_shoulders.py."""

import json
from pathlib import Path

SRC = Path("src/anime_character_creator/character.py")
sh = json.load(open("out/clothes/shoulders.json"))


def pt(p):
    return f"({p[0]:.3f}, {p[1]:.3f})"


def chain(c, pad):
    rows = [f"{pad}(", f"{pad}    {pt(c['start'])},", f"{pad}    ["]
    rows += [f"{pad}        ({pt(a)}, {pt(b)})," for a, b in c["segs"]]
    return rows + [f"{pad}    ],", f"{pad}),"]


s = SRC.read_text()
a = s.index('    "open_jacket": GarmentCut(')
b = s.index("\n}\n", a)
rows = ['    "open_jacket": GarmentCut(', "        fills=("]
rows += chain(sh["jacket_left"], " " * 12) + chain(sh["jacket_right"], " " * 12)
rows += ["        ),", "    ),"]
s = s[:a] + "\n".join(rows) + s[b:]
a = s.index('    "wide": SleeveCut(')
b = s.index("        cuff=", a)
rows = ['    "wide": SleeveCut(', f'        pivot={pt(sh["joint"])},', "        wrist=(1.054, 3.212),", "        half_w=0.20982,", "        sleeve="]
rows += chain(sh["sleeve"], "        ")
s = s[:a] + "\n".join(rows) + "\n" + s[b:]
SRC.write_text(s)
print("emitted")
