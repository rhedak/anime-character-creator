"""Emit the traced katana as character.py source, before `def _arms(`.

Re-running replaces the previously emitted block (between the BEGIN line and the
END marker). The functions that use it (`_katana_placement`, `_katana`) are
written by hand after the END marker and are not touched.
"""

import json
import re

SRC = "/Users/henrik/git/anime-character-creator/src/anime_character_creator/character.py"
OUT = "out/katana"
BEGIN = "# Satoshi's katana, traced per `.claude/skills/trace-reference/SKILL.md`"
END = "# (end of the traced katana)"
data = json.load(open(f"{OUT}/katana_trace.json"))
land = data["landmarks"]


def pt(p):
    return f"({p[0]:.3f}, {p[1]:.3f})"


def chain_rows(c, indent):
    pad = " " * indent
    rows = [f"{pad}{pt(c['start'])},", f"{pad}["]
    rows += [f"{pad}    ({pt(a)}, {pt(b)})," for a, b in c["segs"]]
    rows.append(f"{pad}],")
    return rows


def chain(name, c, comment):
    rows = [f"# {ln}" for ln in comment]
    rows.append(f"{name}: Chain = (")
    rows += chain_rows(c, 4)
    rows.append(")")
    return "\n".join(rows)


def chains(name, cs, comment):
    rows = [f"# {ln}" for ln in comment]
    rows.append(f"{name}: list[Chain] = [")
    for c in cs:
        rows.append("    (")
        rows += chain_rows(c, 8)
        rows.append("    ),")
    rows.append("]")
    return "\n".join(rows)


tsuba_x, tsuba_y = land["tsuba_ref"]
belt = land["belt_ref"]
ground = 7.137  # the reference's soles, measured on the composite's boots
hip_x = tsuba_x / belt["half_w"]
hip_y = tsuba_y - belt["centre_y"]

HEADER = f"""{BEGIN}
# from `ref-local/satoshi-tall-chibi-katana/` (`satoshi-tall-chibi-sword.png` and
# its `segments/`, which are exact crops of it: `katana.png` matches the composite
# to 0.6 of an RGB level at offset (673, 584)), on this figure's own calibration:
# head centre (626, 308), 171.5 px per head radius (the widest row of face skin
# gives 170.5 and the same figure's earlier composite 172; see
# `harness/body/satoshi_tall_chibi_landmarks.py`). The regions are the reference's
# own fills: the scabbard, its two rings and the end cap, the guard, the collar,
# the handle's wrap, ten cream diamonds and the pommel cap, each grown by half the
# outline's width so the boundary lands on the stroke's centre line. The shading
# (the scabbard's highlight stripe, the guard's engraving, the wrap's weave) is
# texture and is not drawn.
#
# Every chain is in the **sword's own frame**, in the reference's head radii:
# origin at the guard's centre, `u` along the scabbard's axis toward the tip, `v`
# across it (the convention `_staff_placement` uses), so a rigid prop can be hung
# at any angle and scale on any figure. `_katana_placement` does that."""

BODY = [
    HEADER,
    f"""# The sword's tilt from vertical in the reference, tip out, and where it hangs on
# the reference's figure: the guard's centre against its belt (as a share of the
# belt's half-width across, and in head radii below the belt's centre), and the
# reference's ground in head radii, so the sword can be scaled with the figure it
# hangs on. The sword runs from the pommel at u = {land["pommel_u"]:.3f} to the tip at u =
# {land["tip_u"]:.3f}, {land["tip_u"] - land["pommel_u"]:.2f} head radii, and the guard is {land["width_v"][1] - land["width_v"][0]:.2f} across.
_KATANA_TILT = {land["tilt_deg"]:.2f}
_KATANA_HIP_X = {hip_x:.3f}
_KATANA_HIP_Y = {hip_y:.3f}
_KATANA_REF_GROUND = {ground:.3f}""",
    chain("_KATANA_SAYA", data["shapes"]["saya"], ["The scabbard: koiguchi ring to kojiri, one silhouette."]),
    chain("_KATANA_RING_DARK", data["shapes"]["ring_dark"], ["The dark ring under the guard."]),
    chain("_KATANA_RING_BROWN", data["shapes"]["ring_brown"], ["The wide brown band under it."]),
    chain("_KATANA_KOJIRI", data["shapes"]["kojiri"], ["The end cap."]),
    chain("_KATANA_TSUBA", data["shapes"]["tsuba"], ["The guard."]),
    chain("_KATANA_FUCHI", data["shapes"]["fuchi"], ["The collar the handle comes out of."]),
    chain("_KATANA_TSUKA", data["shapes"]["tsuka"], ["The handle's silhouette, wrap and diamonds together."]),
    chains(
        "_KATANA_DIAMONDS",
        data["diamonds"],
        ["The cream rayskin diamonds showing through the wrap, top to bottom; the first",
         "and last are the partial ones at the ends."],
    ),
    chain("_KATANA_KASHIRA", data["shapes"]["kashira"], ["The pommel cap."]),
    END,
]
block = "\n\n".join(BODY) + "\n"

src = open(SRC).read()
if BEGIN in src:
    a = src.index(BEGIN)
    b = src.index(END) + len(END) + 1
    src = src[:a] + block + src[b:]
else:
    marker = "def _arms(sk: Skeleton, p: CharacterParams) -> str:"
    src = src.replace(marker, block + "\n\n" + marker, 1)
open(SRC, "w").write(src)
print("emitted", len(block.splitlines()), "lines; sampled colours", data["colours"])
print("hip", hip_x, hip_y)
assert re.search(r"^_KATANA_SAYA: Chain", src, re.M)
