"""The footprint gate of `docs/hands-plan.md`, per candidate.

    ./harness/run.sh harness/hands/metrics.py mitten traced [more candidates]
    ./harness/run.sh harness/hands/metrics.py --all-presets mitten traced

Isolates each hand's own SVG, rasterises it alone and measures it: bounding-box
height and width in head radii, height over width, skin area, the share of the
hand's pixels that are outline, and the narrowest skin run in the fingers in
outline widths. Then says which of the gate's four measures hold.

By default it measures the five sheet presets and prints one line per candidate
and preset (the left hand, then the right when it differs). `--all-presets`
measures all of them and collapses identical lines, which is how the audit found
that the numbers do not depend on the preset.
"""

import sys

from candidates import CANDIDATES, pick
from handlib import JOIN_VS_MITTEN, c, GATE, SHEET_PRESETS, all_presets, footprint, gate_verdict, hand_arrays

COLS = ("height", "width", "aspect", "skin_area", "ink_share", "narrowest_run", "join_vs_mitten")


def measure(p, cand):
    arrs, sk, q, outline_px = hand_arrays(p, cand)
    base_arrs, bsk, bq, bpx = hand_arrays(p, CANDIDATES["mitten"])
    out = {}
    for side, a in arrs.items():
        m = footprint(a, q.skin_tone, sk.head_r, outline_px)
        mitten = footprint(base_arrs[side], bq.skin_tone, bsk.head_r, bpx)
        m["join_vs_mitten"] = m["join"] / mitten["join"]
        # The gate is for hanging hands. A hand gripping a staff is judged by eye (V5, V6).
        m["grip"] = c._fist_grips(q, side)
        out[side] = m
    return out


def fmt(m):
    return " ".join(f"{m[k]:6.3f}" if k != "ink_share" else f"{100 * m[k]:5.1f}%" for k in COLS)


def main():
    args = sys.argv[1:]
    every = "--all-presets" in args
    args = [a for a in args if a != "--all-presets"]
    if not args:
        raise SystemExit(__doc__)
    cands = pick(args)
    names = list(all_presets()) if every else list(SHEET_PRESETS)
    print("gate:", {k: (lo, hi) for k, (lo, hi) in GATE.items()}, "join_vs_mitten:", JOIN_VS_MITTEN)
    print(f"{'candidate':8s} {'hand'}  " + " ".join(f"{k[:6]:>6s}" for k in COLS) + "  gate   [presets]")
    for cand in cands:
        groups: dict = {}
        for name in names:
            res = measure(all_presets()[name], cand)
            for side in sorted(res, reverse=True):
                m = res[side]
                if not m:
                    continue
                key = (side, tuple(round(m[k], 2) for k in COLS)) if every else (side, name)
                if key in groups:
                    groups[key][1].append(name)
                    continue
                bad = [k for k, ok in gate_verdict(m).items() if not ok]
                if not JOIN_VS_MITTEN[0] <= m["join_vs_mitten"] <= JOIN_VS_MITTEN[1]:
                    bad.append("join")
                verdict = "grip, judged by eye" if m["grip"] else ("PASS" if not bad else "fails " + ",".join(bad))
                groups[key] = (f"{cand.label:8s} {'R' if side == 1 else 'L'}  {fmt(m)}  {verdict}", [name])
        for line, who in groups.values():
            print(f"{line}   [{', '.join(who)}]")


if __name__ == "__main__":
    main()
