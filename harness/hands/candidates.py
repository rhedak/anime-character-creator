"""The registry of hand candidates the sheet and the metrics compare.

Letters are what the owner answers with at a checkpoint (the order on the command
line). Since 2026-10-08 every hand the campaign built is a real style in `src/`
(`HAND_STYLES`, `GRIP_STYLES`, `docs/hands-plan.md`), so a candidate is just a way of
setting `hand_style` and `grip_style`. The patch-in prototypes they began as are gone;
`variants.py` says what became what.

A new idea still starts as a code variant: give `Candidate` a `patch` context manager
that patches `character` while it renders, as the prototypes did.
"""

from dataclasses import replace

from handlib import Candidate


def _hands(style: str = "mitten", grip: str = "mitten"):
    return lambda p: replace(p, hand_style=style, grip_style=grip)


# What ships by default, always first so the owner has the baseline beside every pick.
MITTEN = Candidate("mitten", "the chibi's mitten, the default", _hands())
NOTCHED = Candidate("notched", "mitten, tip cut into three fingers (K1)", _hands("notched"))
STROKED = Candidate("stroked", "mitten silhouette, two finger strokes (K2)", _hands("stroked"))
CURLED = Candidate("curled", "half-closed hand (K3)", _hands("curled"))
OPEN = Candidate("open", "the traced open hand, widened and squared at the wrist (W3)", _hands("traced"))
# The staff hand. Same relaxed hand on the other side, so only Katherina's staff arm differs.
FIST = Candidate("fist", "the canon's fist on a held staff, upright against the swing (G2)", _hands("mitten", "fist"))

CANDIDATES: dict[str, Candidate] = {k.label: k for k in (MITTEN, NOTCHED, STROKED, CURLED, OPEN, FIST)}


def pick(labels: list[str]) -> list[Candidate]:
    missing = [x for x in labels if x not in CANDIDATES]
    if missing:
        raise SystemExit(f"unknown candidate(s) {missing}; known: {sorted(CANDIDATES)}")
    return [CANDIDATES[x] for x in labels]
