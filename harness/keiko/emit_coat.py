"""Emit Keiko's lab coat as `character.py` source, before `def _arms(`.

Two kinds of shape, and the difference is the point (`docs/keiko-clothes-plan.md`,
K2, the owner's call on 2026-09-21):

- **The lapels are traced**, off `segments/white-lab-coat.png`, which shows them
  unoccluded. A stepped notch is the one shape here that is miserable to
  eyeball, and it is the shape that makes the front read as tailored.
- **The panels are constructed** from the profile `landmarks.py` measures, not
  walked from pixels. The reference draws the coat and its sleeve as one fill,
  so a traced panel has to infer where the sleeve ends, and the shoulder is
  under the hair and not in the image at all. Every attempt at that boundary
  left stair-steps at the armpit; the measured profile has none of that
  problem, because the opening, the flare and the hem are all measurable where
  the reference actually shows them.

Coordinates are cut coordinates: head radii on `_GARMENT_REF_BODY`
(`tall_chibi`), so the reference's own head radii are squashed about the chin
by `SQUASH` first. Re-running replaces the previously emitted block.
"""

import json
from pathlib import Path

SRC = "src/anime_character_creator/character.py"
BEGIN = "# Keiko's lab coat, per `docs/keiko-clothes-plan.md` K2."
END = "# (end of the lab coat)"
data = json.load(open("out/keiko/coat_trace.json"))
SQUASH = data["squash"]


def cut_y(y):
    """The reference's own head radii -> the cut frame's."""
    return 1.0 + (y - 1.0) * SQUASH


# The front opening, as its half-width against height, measured clear of the
# belt (`landmarks.py`). It narrows to the waist and widens below: that one
# reversal is what reads as tailoring, and the shared `_coat` has no such
# thing, opening steadily from throat to hem.
OPENING = [(0.997, 0.290), (2.000, 0.226), (2.501, 0.228), (2.997, 0.245), (3.499, 0.271), (4.000, 0.302), (4.501, 0.330), (4.900, 0.348)]
# The outer edge. Below the sleeve's end it is measured; above it the sleeve
# covers the panel's own edge in the reference, so those rows are a gentle
# taper from the shoulder to where the measurement picks up, which is the one
# inferred run in this cut and is flagged in the plan's risks.
OUTER = [(1.387, 0.941), (2.383, 0.862), (2.840, 0.842), (3.580, 0.845), (4.227, 1.132), (4.503, 1.169)]
HEM = 4.658  # the reference's 4.969, squashed
SHOULDER = (1.387, 0.941)
THROAT = (0.997, 0.290)
COLLAR_TIP = 0.810  # the lapel's point, the coat's topmost ink


def seg(a, b):
    """A straight segment: a quadratic whose control sits at the midpoint."""
    return (((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b)


def panel(side):
    """One front panel, outer edge down and inner edge back up.

    `side` is +1 for the viewer's right. The hem's corner is rounded rather
    than cut square, which the reference does and the shared `_coat` does not:
    its half-width falls from 1.169 to 0.924 over the last 0.07 head radii.
    """

    def p(x, y):
        return (side * x, y)

    pts = [p(THROAT[1], THROAT[0]), p(SHOULDER[1], SHOULDER[0])]
    pts += [p(w, y) for y, w in OUTER[1:]]
    corner = p(0.924, HEM - 0.02)
    inner = [(y, w) for y, w in OPENING if y > 3.0][::-1]
    chain = []
    prev = pts[0]
    for q in pts[1:]:
        chain.append(seg(prev, q))
        prev = q
    # Round the hem's corner with one curve through the turn, then run the hem
    # in to the opening and back up the front edge.
    chain.append((p(1.169, HEM), corner))
    prev = corner
    for q in [p(w, min(y, HEM)) for y, w in inner]:
        chain.append(seg(prev, q))
        prev = q
    for y, w in [(y, w) for y, w in OPENING if y <= 3.0][::-1]:
        q = p(w, y)
        chain.append(seg(prev, q))
        prev = q
    chain.append(seg(prev, pts[0]))
    return pts[0], chain


def fmt(pt):
    return f"({pt[0]:.3f}, {pt[1]:.3f})"


def rows(start, segs, indent):
    pad = " " * indent
    out = [f"{pad}{fmt(start)},", f"{pad}["]
    out += [f"{pad}    ({fmt(a)}, {fmt(b)})," for a, b in segs]
    out.append(f"{pad}],")
    return out


def const(name, start, segs, comment):
    out = [f"# {ln}" for ln in comment]
    out.append(f"{name}: Chain = (")
    out += rows(start, segs, 4)
    out.append(")")
    return "\n".join(out)


blocks = [
    f"""{BEGIN}
# The panels are built from the profile measured in `harness/keiko/landmarks.py`
# and the lapels are traced off `ref-local/keiko-tall-chibi/segments/white-lab-coat.png`;
# `harness/keiko/emit_coat.py` writes this block and says why the two differ.
# Cut coordinates, head radii on `_GARMENT_REF_BODY`: the reference stands 3.68
# heads against its 3.47, so every height here is the reference's squashed about
# the chin by {SQUASH:.4f}. The collar's point reaches {COLLAR_TIP:.3f}.""",
]
for side, name in ((-1, "LEFT"), (1, "RIGHT")):
    start, segs = panel(side)
    blocks.append(
        const(
            f"_LAB_COAT_PANEL_{name}",
            start,
            segs,
            [f"The {name.lower()} front panel: throat, shoulder, outer edge, rounded hem corner,"]
            + ["and back up the front opening."],
        )
    )
for name in ("left", "right"):
    ch = data["shapes"][f"lapel_{name}"]
    blocks.append(
        const(
            f"_LAB_COAT_LAPEL_{name.upper()}",
            tuple(ch["start"]),
            [(tuple(a), tuple(b)) for a, b in ch["segs"]],
            [f"The {name} lapel facing, traced: collar point, the notch's step, and down"]
            + ["to where the facing ends above the belt."],
        )
    )
blocks.append(END)
block = "\n\n".join(blocks) + "\n"

src = Path(SRC).read_text()
if BEGIN in src:  # drop the previous block wherever it sits, then re-insert
    a, b = src.index(BEGIN), src.index(END) + len(END) + 1
    src = src[:a].rstrip("\n") + "\n\n\n" + src[b:].lstrip("\n")
# Before the registry that holds the cut, not before `_arms`: the constants
# are referenced when `COAT_CUTS` is built at import.
marker = "COAT_CUTS: dict[str, GarmentCut] = {"
src = src.replace(marker, block + "\n\n" + marker, 1)
Path(SRC).write_text(src)
print("emitted", len(block.splitlines()), "lines")
