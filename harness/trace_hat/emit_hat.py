"""Emit the traced hat as character.py source and splice it over the old block."""

import json

SRC = "/Users/henrik/git/anime-character-creator/src/anime_character_creator/character.py"
OUT = "out/trace_hat"
data = json.load(open(f"{OUT}/hat_trace.json"))


def pt(p):
    return f"({p[0]:.3f}, {p[1]:.3f})"


def chain(name, c, comment=None):
    lines = []
    if comment:
        lines += [f"# {ln}" for ln in comment]
    lines.append(f"{name}: Chain = (")
    lines.append(f"    {pt(c['start'])},")
    lines.append("    [")
    for ctrl, end in c["segs"]:
        lines.append(f"        ({pt(ctrl)}, {pt(end)}),")
    lines.append("    ],")
    lines.append(")")
    return "\n".join(lines)


HEADER = """# A pointed witch's hat, traced per `.claude/skills/trace-reference/SKILL.md`
# from `../time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg`
# (`docs/katherina-accessories-plan.md`, milestone 2).
#
# Every chain below is the reference's own contour, not a hand-placed landmark.
# The reference's fills are separated by black outline on a black page, so each
# region (crown, band, the three pieces of the bow, the brim's top surface, the
# two patches of underside showing at the brim's tips) is its own connected
# component of non-outline pixels. Each was grown back by half the reference's
# outline width, so its boundary lands on the stroke's centre line where this
# code draws its own, walked with `trace_lib.boundary`, then simplified and
# least-squares fitted with `trace_lib.fit_closed`. The three crease strokes
# near the curl are the outline-coloured ink left inside the crown.
#
# Calibration is off the face, which is what the hat has to fit: the
# reference's widest face row and its chin against this generator's own chibi
# face (rendered, measured in head radii) give 173.7 px per head radius on both
# axes, and the two axes agreeing is what says it is right, with the head
# centre at (650, 481) in the reference's pixels. An earlier pass calibrated off
# an eye-centre x that was really between the left eye and the nose, and an
# eye-to-chin run that assumed proportions the chibi does not have (142.9 px,
# centre 45 px too far left), then shrank the result by a different factor per
# axis to fit the canvas: that is why it came out small, squat and off to one
# side.
#
# Nothing is rescaled here. The reference's crown stands 2.6 head radii above
# the head centre, far above any haircut's headroom, and the canvas makes room
# for the hat rather than the hat for the canvas: `hat_hair_margin` below is
# what `build_skeleton` is handed where a character's skeleton is built, so a
# hat-wearer's figure stands a little smaller on the same canvas. The brim's
# front rim crosses the head's centre line at -1.0, the top of the skull, which
# puts it over the crown of every haircut here: the hair goes under the hat and
# comes out below the brim, as in the reference.
Chain = tuple[Point, list[Segment]]"""

parts = [HEADER]
parts.append(
    chain(
        "_HAT_UNDERSIDE",
        data["back"],
        [
            "The brim's underside, drawn behind the hair (`_hat_underside`): the whole",
            "silhouette, carried on across behind the head along the hull of the two",
            "patches of underside the reference shows at the tips. Our hair is not the",
            "reference's and is narrower under the brim, and where it does not reach",
            "this is what shows, as it would under a real brim, rather than the page.",
        ],
    )
)
parts.append(
    chain(
        "_HAT_BRIM",
        data["brim"],
        [
            "Everything in front of the hair: the brim's top surface with the crown,",
            "band and bow on it. Its lower edge is the brim's front rim, over the hair.",
        ],
    )
)
parts.append(
    chain(
        "_HAT_CROWN",
        data["crown"],
        [
            "Leans right, kinks, and curls into a hooked tip. Its lower edge is the",
            "band's upper one.",
        ],
    )
)
parts.append(chain("_HAT_BAND", data["band"]))
lines = [
    "# The bow on the band's right: a wide loop, a narrow wrap, and the tail, each",
    "# its own piece of the band's cloth.",
    "_HAT_BUCKLE: list[Chain] = [",
]
for c in (data[f"buckle{i}"] for i in range(3)):
    lines.append(f"    ({pt(c['start'])}, [")
    for ctrl, end in c["segs"]:
        lines.append(f"        ({pt(ctrl)}, {pt(end)}),")
    lines.append("    ]),")
lines.append("]")
parts.append("\n".join(lines))
lines = [
    "# Crease strokes where the crown folds under its curl. Open lines, not shapes.",
    "_HAT_CREASES: list[Chain] = [",
]
for c in data["creases"]:
    segs = ", ".join(f"({pt(ctrl)}, {pt(end)})" for ctrl, end in c["segs"])
    lines.append(f"    ({pt(c['start'])}, [{segs}]),")
lines.append("]")
parts.append("\n".join(lines))

FUNCS = '''

def hat_hair_margin(p: CharacterParams) -> float:
    """Headroom, in head radii above the skull, that `p`'s hat needs; 0 for none.

    For `build_skeleton`'s `min_hair_margin`: the canvas grows room for the hat
    instead of the hat being squashed under a ceiling set for hair. The fitted
    chain's controls are included, which bounds the curve (a quadratic never
    leaves its control triangle), plus the stroke's outer half and a hair of
    air.
    """
    if p.outfit.hat_color is None:
        return 0.0
    start, segs = _HAT_BRIM
    top = min(start[1], *(y for c, e in segs for y in (c[1], e[1])))
    return -top - 1.0 + 0.06


def _hat_underside(sk: Skeleton, p: CharacterParams) -> str:
    """The underside of a hat's brim, behind the hair and everything else.

    A brim is a disc around the head, and the head and hair come in front of
    its far side. Drawn first, so the hair, face and body cover it, and what is
    left showing is the underside where the brim droops at its tips and
    wherever the hair falls short of the brim. `_hat` draws the near side over
    the hair at the end.
    """
    if p.outfit.hat_color is None:
        return ""
    d = _curve(sk.head_cx, sk.head_cy, sk.head_r, *_HAT_UNDERSIDE)
    fill = shade(p.outfit.hat_color, value_factor=0.62)
    return f'<path d="{d}" fill="{fill}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'


def _hat(sk: Skeleton, p: CharacterParams) -> str:
    """A pointed witch's hat's near side: brim, crown, band and bow, over everything.

    Over the hair mass and the fringe both, the way the headscarf sits over
    them: a hat is put on, not grown, and it covers what it is put over. It
    does not size itself off `_hair_edge_x` the way the headscarf does: its
    shape is the reference's (see the comment above `_HAT_UNDERSIDE`), and the
    brim is wide enough that every haircut's crown is under it. The far side
    of the brim is `_hat_underside`, at the back of the figure.

    Back to front: the brim's top surface with the whole hat above it in the
    hat colour, the crown over that, the band and its bow in the band colour,
    and the creases last, as line work.
    """
    if p.outfit.hat_color is None:
        return ""
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    color = p.outfit.hat_color
    sw = _stroke_w(sk)

    def shape(chain: Chain, fill: str) -> str:
        d = _curve(cx, cy, r, *chain)
        return f'<path d="{d}" fill="{fill}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'

    parts = [shape(_HAT_BRIM, color), shape(_HAT_CROWN, color)]
    band_color = p.outfit.hat_band_color
    if band_color is not None:
        parts.append(shape(_HAT_BAND, band_color))
        parts.extend(shape(piece, band_color) for piece in _HAT_BUCKLE)
    for crease in _HAT_CREASES:
        d = _curve(cx, cy, r, *crease, close=False)
        parts.append(
            f'<path d="{d}" fill="none" stroke="{OUTLINE}" stroke-width="{sw * 0.8:.1f}" '
            'stroke-linecap="round" />'
        )
    return "".join(parts)
'''

block = "\n\n".join(parts) + "\n" + FUNCS
src = open(SRC).read().split("\n")
start = next(i for i, ln in enumerate(src) if ln.startswith("# A pointed witch's hat, traced per"))
end = next(i for i, ln in enumerate(src) if i > start and ln == '    return "".join(parts)')
new = src[:start] + block.rstrip("\n").split("\n") + src[end + 1 :]
text = "\n".join(new)
if "_hat_underside(sk, p)," not in text:
    old = "        _hair_defs(sk, p),\n"
    assert text.count(old) == 1
    text = text.replace(
        old,
        old + "        # The far side of a hat's brim, behind the hair, the head and everything.\n"
        "        _hat_underside(sk, p),\n",
    )
open(SRC, "w").write(text)
print("replaced lines", start + 1, "to", end + 1)
