"""D4d H2 of `docs/detail-plan.md`: emit the traced hands as character.py source.

Reads `out/trace_hands/hands.json` (`trace_hands.py`) and writes the poses as
module constants, inserted before `def _hand(`. Re-running replaces the block
between its two marker lines, so a retrace is: run `trace_hands.py`, run this,
`ruff format`, render.
"""

import json

SRC = "src/anime_character_creator/character.py"
OUT = "out/trace_hands"
BEGIN = "# Two hands, traced per `.claude/skills/trace-reference/SKILL.md`"
END = "# (end of the traced hands)"


def pt(p):
    return f"({p[0]:.4f}, {p[1]:.4f})"


def chain(c, pad):
    start, segs = c
    rows = [f"{pad}(", f"{pad}    {pt(start)},", f"{pad}    ["]
    rows += [f"{pad}        ({pt(a)}, {pt(b)})," for a, b in segs]
    rows += [f"{pad}    ],", f"{pad}),"]
    return rows


def pose(name, data):
    rows = [f"{name}: tuple[HandPiece, ...] = ("]
    for piece in data["pieces"]:
        rows.append("    (")
        rows += chain(piece["outline"], "        ")
        rows.append("        (")
        for h in piece["holes"]:
            rows += chain(h, "            ")
        rows.append("        ),")
        rows.append("        (")
        for ln in piece["lines"]:
            rows += chain(ln, "            ")
        rows.append("        ),")
        rows.append("    ),")
    rows.append(")")
    return rows


def main():
    data = json.load(open(f"{OUT}/hands.json"))
    lines = [
        BEGIN,
        "# off `ref-local/katherina_grok_real/` (`docs/detail-plan.md`, D4d; the scripts",
        "# in `harness/trace_hands/`): her left hand hanging (`relaxed`, the viewer's",
        "# right) and her right hand round the staff (`grip`, the viewer's left). Each is",
        "# its pieces in drawing order, every piece its outline, its holes (the page",
        "# showing through) and its interior lines, grown to the stroke's centre line.",
        "# Points are relative to the wrist's centre where the skin meets the cuff, in",
        "# the picture's own axes (x right, y down), in units of the hand's length.",
        "# Emitted by `harness/trace_hands/emit_hands.py`; do not edit by hand.",
        "HandPiece = tuple[Chain, tuple[Chain, ...], tuple[Chain, ...]]",
        "",
    ]
    for key, const in (("relaxed", "_HAND_RELAXED"), ("grip", "_HAND_GRIP")):
        lines += pose(const, data[key])
        lines.append("")
    lines.append(END)
    block = "\n".join(lines) + "\n"
    src = open(SRC).read()
    if BEGIN in src:
        a = src.index(BEGIN)
        b = src.index(END) + len(END) + 1
        src = src[:a] + block + src[b:]
    else:
        at = src.index("def _hand(\n")
        src = src[:at] + block + "\n\n" + src[at:]
    open(SRC, "w").write(src)
    print("emitted", len(block.splitlines()), "lines")


if __name__ == "__main__":
    main()
