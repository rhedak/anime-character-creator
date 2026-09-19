"""Write `out/kou/kou.json` into character.py as the familiar's shape block."""

import json
from pathlib import Path

SRC = Path("src/anime_character_creator/character.py")
d = json.load(open("out/kou/kou.json"))
BEGIN = "# Kou, Katherina's bat familiar, traced per"
END = "# (end of the traced familiar)"


def pt(p):
    return f"({p[0]:.3f}, {p[1]:.3f})"


def chain(c, pad):
    rows = [f"{pad}(", f"{pad}    {pt(c['start'])},", f"{pad}    ["]
    rows += [f"{pad}        ({pt(a)}, {pt(b)})," for a, b in c["segs"]]
    return rows + [f"{pad}    ],", f"{pad}),"]


def chains(name, cs, comment):
    rows = [f"# {ln}" for ln in comment] + [f"{name}: list[Chain] = ["]
    for c in cs:
        rows += chain(c, "    ")
    return "\n".join(rows + ["]"])


def one(name, c, comment):
    rows = [f"# {ln}" for ln in comment] + [f"{name}: Chain = ("]
    rows += chain(c, "")[1:-1]
    return "\n".join(rows + [")"])


head = f"""{BEGIN} `.claude/skills/trace-reference/SKILL.md`
# from `../time_slider_katherina/style-anchors/kou_grok/kou.png`
# (`docs/katherina-accessories-plan.md`, milestone 4). That reference was
# generated to be traced: flat single-tone surfaces, pure-black outlines, a
# light background and nothing overlapping him, so every shape below is one of
# its own fill regions, with nothing inferred anywhere
# (`harness/kou/trace_kou.py`).
#
# Coordinates are in wingspan units, 1.0 tip to tip, origin at the centre of his
# bounding box, so where he goes is two numbers: `_KOU_SPAN` (how wide he is in
# head radii) and `_KOU_CENTRE`. The book: "a magical bat-like creature, not a
# mundane bat", small and dark-furred, black-eyed (Mori's are "paler than Kou's,
# more silver than black"), ears that angle and point since his echolocation is
# his magic-detection sense, wingspan "over a foot". He flies here rather than
# perching on her shoulder, the owner's call on 2026-09-19; that also keeps him
# independent of the shoulder, so nothing about him has to follow the hair.
#
# Mori is the same creature colour-inverted (`design.md`'s eyes-constant,
# surface-traits-vary rule), so the colours are fields and the shape is shared.
_KOU_SPAN = 2.0
_KOU_CENTRE: Point = (1.62, 0.85)"""

parts = [head]
parts.append(one("_KOU_BODY", d["body"], ["Head, ears and feet in one fill, as the reference draws them."]))
parts.append(chains("_KOU_WINGS", [d["wing_left"], d["wing_right"]], ["Each wing whole, drawn under its own cells."]))
parts.append(
    chains(
        "_KOU_WING_CELLS",
        d["wing_left_cells"] + d["wing_right_cells"],
        [
            "The cells the finger struts divide each wing into. Drawn over the wing,",
            "each with its own outline, they are what makes the struts.",
        ],
    )
)
parts.append(chains("_KOU_EYES", d["eyes"], ["Two black discs. Their own colour, so Mori's can be silver."]))
parts.append(chains("_KOU_LINES", d["lines"], ["The ink inside him: both ear ridges, the nose, the mouth."]))

FUNCS = '''

def _familiar(sk: Skeleton, p: CharacterParams) -> str:
    """A small bat familiar in flight, beside the figure's left shoulder.

    Drawn last of everything: he is beside her rather than worn, so nothing on
    the figure should cross him. Placed by `_KOU_SPAN`/`_KOU_CENTRE` in head
    radii, which is all a hovering creature needs: no contact geometry where
    feet would meet a shoulder, and no dependence on where the hair ends.
    """
    fur = p.familiar_color
    if fur is None:
        return ""
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    sw = _stroke_w(sk)
    ox, oy = _KOU_CENTRE

    def xf(pt: Point) -> Point:
        return (ox + pt[0] * _KOU_SPAN, oy + pt[1] * _KOU_SPAN)

    def d(chain: Chain, close: bool = True) -> str:
        start, segs = chain
        return _curve(cx, cy, r, xf(start), [(xf(c), xf(e)) for c, e in segs], close=close)

    parts = [
        f\'<path d="{d(shape)}" fill="{fur}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />\'
        for shape in (*_KOU_WINGS, *_KOU_WING_CELLS, _KOU_BODY)
    ]
    parts.extend(
        f\'<path d="{d(eye)}" fill="{p.familiar_eye_color or OUTLINE}" stroke="{OUTLINE}" \'
        f\'stroke-width="{sw * 0.5:.1f}" />\'
        for eye in _KOU_EYES
    )
    parts.extend(
        f\'<path d="{d(line, close=False)}" fill="none" stroke="{OUTLINE}" \'
        f\'stroke-width="{sw * 0.7:.1f}" stroke-linecap="round" />\'
        for line in _KOU_LINES
    )
    return "".join(parts)
'''

block = "\n\n".join(parts) + "\n" + FUNCS + "\n\n" + END + "\n"
s = SRC.read_text()
if BEGIN in s:
    s = s[: s.index(BEGIN)] + block + s[s.index(END) + len(END) + 1 :]
else:
    anchor = "def render_character(\n"
    assert s.count(anchor) == 1
    s = s.replace(anchor, block + "\n\n" + anchor)
SRC.write_text(s)
print("emitted")
