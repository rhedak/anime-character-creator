"""D5 plan, step 3, part 3: `trace.json` as the `character.py` block for the
parted cut, so a retrace is trace, emit, paste, render.

Prints the block between the two marker comments in `character.py`; with
`--write` replaces what is between them in place.

    ./harness/run.sh harness/hair_parted/emit.py [--write]
"""

import json
import pathlib
import sys

SRC = pathlib.Path("src/anime_character_creator/character.py")
BEGIN = "# BEGIN parted trace (harness/hair_parted/emit.py)"
END = "# END parted trace"


def pt(p):
    return f"({p[0]:.3f}, {p[1]:.3f})"


def chain(name, ch, doc):
    start, segs = ch
    out = [f"# {doc}", f"{name}: Chain = (", f"    {pt(start)},", "    ["]
    out += [f"        ({pt(c)}, {pt(e)})," for c, e in segs]
    out += ["    ],", ")"]
    return out


def block(t):
    lines = [BEGIN]
    lines += chain(
        "_PARTED_EDGE",
        t["mass"],
        "The silhouette, from the left outer fall's inner tip up the left side, over the crown and down to the right's.",
    )
    lines += [
        "# Which segments of `_PARTED_EDGE` end on the left seam's outer end, the crown's apex and the right seam's.",
        f"_PARTED_SEAM_L = {t['mass_seam_l']}",
        f"_PARTED_CROWN_AT = {t['mass_crown']}",
        f"_PARTED_SEAM_R = {t['mass_seam_r']}",
        "# The lowest point of the trace, which `fall` scales against.",
        f"_PARTED_BASE_TIP = {t['base_tip']:.3f}",
    ]
    lines += chain(
        "_PARTED_LINE",
        t["line"],
        "The hairline, from the left front lock's lowest tip up past the face and down to the right's.",
    )
    lines += chain("_PARTED_LOCK_L", t["lock_l"], "The left front lock's outer edge, from the seam's inner end to its tip.")
    lines += chain("_PARTED_LOCK_R", t["lock_r"], "The right front lock's outer edge, from the seam's inner end to its tip.")
    lines += [
        "# Which segment of each lock's edge ends where the dark strip opens beside it.",
        f"_PARTED_APEX_L = {t['lock_apex_l']}",
        f"_PARTED_APEX_R = {t['lock_apex_r']}",
    ]
    lines += chain("_PARTED_UNDER_L", t["under_l"], "The left outer fall's inner edge, from the dark strip's top to its tip.")
    lines += chain("_PARTED_UNDER_R", t["under_r"], "The right outer fall's inner edge, from the dark strip's top to its tip.")
    tips = json.load(open("out/hair_parted/tips.json"))
    for name, key, doc in (
        ("_PARTED_TIPS_BEHIND", "behind", "The outer falls' tips (`tips_find.py`), drawn with the mass: apex and direction."),
        ("_PARTED_TIPS_FRONT", "front", "The front's tips, drawn with it: apex and direction."),
    ):
        lines += [f"# {doc}", f"{name}: list[tuple[Point, Point]] = ["]
        lines += [f"    ({pt(a)}, {pt(d)})," for a, d in tips[key]]
        lines.append("]")
    lines.append(END)
    return "\n".join(lines)


def main() -> None:
    t = json.load(open("out/hair_parted/trace.json"))
    text = block(t)
    if "--write" in sys.argv:
        src = SRC.read_text()
        a, b = src.index(BEGIN), src.index(END) + len(END)
        SRC.write_text(src[:a] + text + src[b:])
        print(f"wrote {SRC}")
    else:
        print(text)


if __name__ == "__main__":
    main()
