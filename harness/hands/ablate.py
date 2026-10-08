"""Two diagnostics from the 2026-10-08 audit (`docs/hands-status.md`).

    ./harness/run.sh harness/hands/ablate.py pieces OUTDIR [PRESET]
        Drop the traced relaxed hand's pieces and interior lines one variant at a
        time and print the outline share of each, so a piece that carries the ink
        shows. The audit's result: dropping the fingertip pieces and the interior
        lines moved it from 45.0% to 42.9%, so they were not the cause.

    ./harness/run.sh harness/hands/ablate.py widen OUTDIR F [F ...]
        The traced relaxed hand with its x scaled by each F about its wrist, next to
        the mitten. Diagnostic only: per-axis scaling is what the trace-reference
        skill forbids, used to ask whether 'too narrow' is the problem. The audit's
        result: it is not, widening fills the hand but it still reads as an adult's.
"""

import os
import sys
from dataclasses import replace

from handlib import Candidate, capture_hands, crop_hand, hand_arrays, label, render
from PIL import Image

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

S = 8


def ink_share(arr):
    nonwhite = (arr < 245).any(axis=2)
    return (arr.sum(axis=2) < 120).sum() / max(1, nonwhite.sum())


def pieces(out, preset):
    orig = c._HAND_RELAXED
    print("pieces:", len(orig))
    for i, (o, h, ln) in enumerate(orig):
        print(f"  piece {i}: outline segs {len(o[1])}, holes {len(h)}, interior lines {len(ln)}")
    variants = {
        "all pieces": orig,
        "outline piece only": orig[:1],
        "no interior lines": tuple((o, h, ()) for o, h, _ in orig),
    }
    traced = replace(PRESETS[preset], hand_style="traced")
    tiles = []
    try:
        for name, pcs in variants.items():
            c._HAND_RELAXED = pcs
            cand = Candidate(name, name, lambda p: replace(p, hand_style="traced"))
            arrs, sk, q, _ = hand_arrays(traced, cand, S)
            print(f"{name:22s} ink share {100 * ink_share(arrs[1]):5.1f}%")
            im, sk, centres = render(traced, S, cand)
            tiles.append(label(crop_hand(im, sk, centres[1], S, 0.9, 300), name))
    finally:
        c._HAND_RELAXED = orig
    sheet = Image.new("RGB", (len(tiles) * 304, 304), "white")
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * 304, 2))
    sheet.save(f"{out}/pieces.png")


def widen(out, factors):
    orig = c._traced_placement
    state = {"f": 1.0}

    def patched(sk, p, side):
        place = orig(sk, p, side)
        f = state["f"]
        return lambda q: place((q[0] * f, q[1]))

    k = PRESETS["krista"]
    tiles = []
    im, sk, centres = render(k, S, Candidate("mitten", "", lambda p: replace(p, hand_style="mitten")))
    tiles.append(label(crop_hand(im, sk, centres[-1], S, 0.9, 300), "mitten"))
    c._traced_placement = patched
    try:
        for f in factors:
            state["f"] = f
            cand = Candidate(f"x{f}", "", lambda p: replace(p, hand_style="traced"))
            im, sk, centres = render(k, S, cand)
            tiles.append(label(crop_hand(im, sk, centres[-1], S, 0.9, 300), f"traced x{f}"))
    finally:
        c._traced_placement = orig
    sheet = Image.new("RGB", (len(tiles) * 304, 304), "white")
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * 304, 2))
    sheet.save(f"{out}/widen.png")


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    mode, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    if mode == "pieces":
        pieces(out, sys.argv[3] if len(sys.argv) > 3 else "krista")
    elif mode == "widen":
        widen(out, [float(x) for x in sys.argv[3:]] or [1.0, 1.3, 1.6])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
